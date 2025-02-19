from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession
from models.video_transcription import VideoTranscription
from sqlalchemy.future import select
import os

REDIS_BROKER = os.getenv("REDIS_BROKER", "redis://localhost:6379/0")
REDIS_BACKEND = os.getenv("REDIS_BACKEND", "redis://localhost:6379/0")

# Configure Celery
celery_app = Celery(
    "worker",
    backend=REDIS_BACKEND,
    broker=REDIS_BROKER
)

@celery_app.task
async def fetch_or_generate_transcript_with_whisper(video_url: str, db: AsyncSession, output_dir: str = "./"):
    video_id = video_url.split("v=")[-1]
    audio_path = os.path.join(output_dir, f"{video_id}.wav")

    # Check if transcription already exists
    existing_transcription = await db.execute(select(VideoTranscription).where(VideoTranscription.video_id == video_id))
    transcription_record = existing_transcription.scalars().first()
    if transcription_record and transcription_record.transcript:
        return {"status": "success", "transcript": transcription_record.transcript}

    # Create a new record for this transcription
    transcription_record = VideoTranscription(video_id=video_id, video_url=video_url, status="pending")
    db.add(transcription_record)
    await db.commit()

    try:
        # Fetch existing YouTube transcript
        from youtube_transcript_api import YouTubeTranscriptApi
        from yt_dlp import YoutubeDL
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en', 'en-US'])
        transcript_text = " ".join([item["text"] for item in transcript.fetch()])
        transcription_record.transcript = transcript_text
        transcription_record.status = "completed"
    except Exception as e:
        # Handle Whisper fallback
        print(f"Falling back to Whisper due to: {e}")
        ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'wav',
            'outtmpl': audio_path,
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Whisper transcription
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            transcription_record.transcript = result["text"]
            transcription_record.status = "completed"
        except Exception as whisper_error:
            transcription_record.status = "error"
            transcription_record.transcript = str(whisper_error)

        # os.remove(audio_path)

    # Update the database
    await db.commit()
    return {"status": transcription_record.status, "transcript": transcription_record.transcript}
