from celery import Celery
from config import get_settings
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.video_transcription import VideoTranscription
from db import async_session
from contextlib import contextmanager
import os
import tempfile
from utils.embeddings import split_transcript_into_chunks
import numpy as np
from asgiref.sync import async_to_sync
from youtube_transcript_api import YouTubeTranscriptApi
import whisper
from typing import List, Tuple
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Celery
celery_app = Celery(
    'video_processor',
    broker=settings.REDIS_BROKER,
    backend=settings.REDIS_BACKEND
)

# Initialize the model (this will download it the first time)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Small, fast model with good performance

@contextmanager
def temporary_file(suffix=None):
    """Context manager for handling temporary files."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        yield temp_file.name
    finally:
        try:
            os.unlink(temp_file.name)
        except Exception as e:
            logger.error(f"Failed to delete temporary file {temp_file.name}: {e}")

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        # If this is not the first chunk, include the overlap
        if start > 0:
            chunk_start = max(start - overlap, 0)
        else:
            chunk_start = start
        chunks.append(text[chunk_start:end])
        start = end - overlap if end < text_length else text_length

    return chunks

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings using sentence-transformers."""
    try:
        # Generate embeddings for all texts at once
        embeddings = embedding_model.encode(texts)
        # Convert numpy arrays to lists for JSON serialization
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Error getting embeddings: {e}")
        raise

@celery_app.task
def fetch_or_generate_transcript_with_whisper(video_url: str):
    try:
        logger.info(f"Starting transcription for video: {video_url}")
        video_id = video_url.split("v=")[1]
        
        @async_to_sync
        async def process_transcription():
            transcript = None
            
            # First try to fetch from YouTube's API
            try:
                transcript = await fetch_youtube_transcript(video_id)
                logger.info("Successfully fetched transcript from YouTube API")
            except Exception as e:
                logger.warning(f"Failed to fetch YouTube transcript: {e}")
                
                # If YouTube transcript fails, use Whisper
                try:
                    with temporary_file(suffix='.wav') as audio_path:
                        await download_audio(video_url, audio_path)
                        transcript = await transcribe_with_whisper(audio_path)
                        logger.info("Successfully generated transcript with Whisper")
                except Exception as e:
                    logger.error(f"Failed to generate transcript with Whisper: {e}")
                    raise

            if transcript:
                # Process transcript into chunks and get embeddings
                chunks = chunk_text(transcript)
                embeddings = get_embeddings(chunks)
                
                # Update database with transcript, chunks, and embeddings
                async with async_session() as db:
                    async with db.begin():
                        result = await db.execute(
                            select(VideoTranscription).where(VideoTranscription.video_id == video_id)
                        )
                        transcription = result.scalar_one_or_none()
                        
                        if transcription:
                            transcription.transcript = transcript
                            transcription.chunks = chunks
                            transcription.embeddings = embeddings
                            transcription.status = "completed"
                            await db.commit()
                            logger.info(f"Successfully saved transcript and embeddings for video {video_id}")
                    
            return {"status": "success", "video_id": video_id}
            
        return process_transcription()
    except Exception as e:
        logger.error(f"Error in transcription task: {e}")
        @async_to_sync
        async def update_error_status():
            async with async_session() as db:
                async with db.begin():
                    result = await db.execute(
                        select(VideoTranscription).where(VideoTranscription.video_id == video_id)
                    )
                    transcription = result.scalar_one_or_none()
                    if transcription:
                        transcription.status = "error"
                        await db.commit()
        
        update_error_status()
        raise

# Helper functions
async def fetch_youtube_transcript(video_id: str) -> str:
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    transcript = transcript_list.find_transcript(['en', 'en-US'])
    return " ".join([item["text"] for item in transcript.fetch()])

async def download_audio(video_url: str, output_path: str):
    from yt_dlp import YoutubeDL
    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'wav',
        'outtmpl': output_path,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

async def transcribe_with_whisper(audio_path: str) -> str:
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]

# curl -X POST http://localhost:8000/auth/login   -H "Content-Type: application/x-www-form-urlencoded"   -d "username=test@example.com&password=your_password"