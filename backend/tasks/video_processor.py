import logging
import os
import subprocess
import tempfile
from contextlib import contextmanager
from typing import List, Tuple

import numpy as np
import whisper
from asgiref.sync import async_to_sync
from celery import Celery
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from youtube_transcript_api import CouldNotRetrieveTranscript, YouTubeTranscriptApi
from yt_dlp import YoutubeDL

from config import get_settings
from db import async_session
from models.video_transcription import TranscriptionStatus, VideoTranscription
from utils.embeddings import split_transcript_into_chunks

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Celery
celery_app = Celery(
    "video_processor", broker=settings.REDIS_BROKER, backend=settings.REDIS_BACKEND
)

# Initialize the model (this will download it the first time)
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)  # Small, fast model with good performance


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

            # First get video metadata
            try:
                with YoutubeDL() as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    title = info.get("title")
                    thumbnail = info.get("thumbnail")
                    logger.info(f"Successfully fetched metadata for video: {title}")
            except Exception as e:
                logger.warning(f"Failed to fetch video metadata: {e}")
                title = None
                thumbnail = None
            # breakpoint()
            # First try to fetch from YouTube's API
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = " ".join(
                    [
                        entry["text"]
                        for entry in transcript_list.find_transcript(["en"]).fetch()
                    ]
                )
                logger.info("Successfully fetched transcript from YouTube API")
            except CouldNotRetrieveTranscript as e:
                logger.warning(f"Failed to fetch YouTube transcript: {e}")

                # If YouTube transcript fails, use Whisper
                try:
                    with temporary_file(suffix=".wav") as audio_path:
                        await download_audio(video_url, audio_path)
                        if os.path.exists(audio_path):
                            transcript = await transcribe_with_whisper(audio_path)
                            logger.info(
                                "Successfully generated transcript with Whisper"
                            )
                        else:
                            raise Exception(f"Audio file not found at {audio_path}")
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
                            select(VideoTranscription).where(
                                VideoTranscription.video_id == video_id
                            )
                        )
                        transcription = result.scalar_one_or_none()

                        if transcription:
                            transcription.transcript = transcript
                            transcription.chunks = chunks
                            transcription.embeddings = embeddings
                            transcription.title = title
                            transcription.thumbnail_url = thumbnail
                            transcription.status = TranscriptionStatus.COMPLETED
                            await db.commit()
                            logger.info(
                                f"Successfully saved transcript and metadata for video {video_id}"
                            )

            return {"status": "success", "video_id": video_id}

        return process_transcription()
    except Exception as e:
        logger.error(f"Error in transcription task: {e}")

        @async_to_sync
        async def update_error_status():
            async with async_session() as db:
                async with db.begin():
                    result = await db.execute(
                        select(VideoTranscription).where(
                            VideoTranscription.video_id == video_id
                        )
                    )
                    transcription = result.scalar_one_or_none()
                    if transcription:
                        transcription.status = TranscriptionStatus.ERROR
                        await db.commit()

        update_error_status()
        raise


# Helper functions
async def download_audio(video_url: str, output_path: str):
    """Download audio from YouTube video using yt-dlp."""
    try:
        # First download the best audio format
        download_command = [
            "yt-dlp",
            "-f",
            "bestaudio",  # Get best audio quality
            "--extract-audio",
            "-o",
            output_path,
            video_url,
        ]

        process = subprocess.Popen(
            download_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(f"yt-dlp download failed: {stderr.decode()}")

        # Get the downloaded file (might have a different extension)
        downloaded_file = None
        for ext in [".webm", ".m4a", ".mp3", ".opus"]:
            if os.path.exists(output_path + ext):
                downloaded_file = output_path + ext
                break

        if not downloaded_file:
            raise Exception("Could not find downloaded audio file")

        # Convert to WAV using ffmpeg
        convert_command = [
            "ffmpeg",
            "-i",
            downloaded_file,
            "-acodec",
            "pcm_s16le",  # Standard WAV codec
            "-ar",
            "16000",  # 16kHz sample rate
            "-ac",
            "1",  # Mono
            "-y",  # Overwrite output file
            output_path,
        ]

        process = subprocess.Popen(
            convert_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(f"ffmpeg conversion failed: {stderr.decode()}")

        # Clean up the original downloaded file
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)

    except Exception as e:
        logger.error(f"Error downloading/converting audio: {e}")
        raise


async def transcribe_with_whisper(audio_path: str) -> str:
    """Transcribe audio file using Whisper."""
    try:
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise


async def process_transcription(video_id: str, video_url: str):
    """Process video transcription including metadata and audio transcription."""
    audio_path = f"temp_{video_id}.wav"

    try:
        # Get video metadata first
        with YoutubeDL() as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get("title")
            thumbnail = info.get("thumbnail")

        async with async_session() as db:
            async with db.begin():
                # Update video with metadata
                result = await db.execute(
                    select(VideoTranscription).where(
                        VideoTranscription.video_id == video_id
                    )
                )
                transcription = result.scalar_one_or_none()
                if transcription:
                    transcription.title = title
                    transcription.thumbnail_url = thumbnail
                    transcription.status = TranscriptionStatus.PENDING
                    await db.commit()

        # Download audio
        await download_audio(video_url, audio_path)

        # Load Whisper model and transcribe
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        transcript_text = result["text"]

        # Update database with transcript
        async with async_session() as db:
            async with db.begin():
                result = await db.execute(
                    select(VideoTranscription).where(
                        VideoTranscription.video_id == video_id
                    )
                )
                transcription = result.scalar_one_or_none()
                if transcription:
                    transcription.transcript = transcript_text
                    transcription.status = TranscriptionStatus.COMPLETED
                    await db.commit()

        logger.info(f"Successfully transcribed video {video_id}")

    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        # Update status to error in database
        async with async_session() as db:
            async with db.begin():
                result = await db.execute(
                    select(VideoTranscription).where(
                        VideoTranscription.video_id == video_id
                    )
                )
                transcription = result.scalar_one_or_none()
                if transcription:
                    transcription.status = TranscriptionStatus.ERROR
                    await db.commit()
        raise

    finally:
        # Clean up temporary audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)


# curl -X POST http://localhost:8000/auth/login   -H "Content-Type: application/x-www-form-urlencoded"   -d "username=test@example.com&password=your_password"
