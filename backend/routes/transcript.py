import logging

from celery.result import AsyncResult
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.video_transcription import TranscriptionStatus, VideoTranscription
from services.auth import get_current_user
from tasks.video_processor import celery_app, fetch_or_generate_transcript_with_whisper

router = APIRouter()
logger = logging.getLogger(__name__)


class TranscriptionRequest(BaseModel):
    video_url: str

    @validator("video_url")
    def validate_youtube_url(cls, v):
        if not VideoTranscription.validate_youtube_url(v):
            raise ValueError("Invalid YouTube URL")
        return v


@router.post("/transcribe")
async def transcribe_video(
    request: TranscriptionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        video_id = request.video_url.split("v=")[1]

        # Check if transcription already exists
        result = await db.execute(
            select(VideoTranscription).where(VideoTranscription.video_id == video_id)
        )
        existing_transcription = result.scalar_one_or_none()

        if existing_transcription:
            # If it exists but is in error state, retry transcription
            if existing_transcription.status == TranscriptionStatus.ERROR:
                existing_transcription.status = TranscriptionStatus.PENDING
                await db.commit()
                fetch_or_generate_transcript_with_whisper.delay(request.video_url)
                return {
                    "status": "processing",
                    "message": "Retrying transcription",
                    "video_id": video_id,
                }

            # If it's pending or completed, return current status
            return {
                "status": existing_transcription.status,
                "message": f"Transcription already {existing_transcription.status}",
                "video_id": video_id,
            }

        # Create new transcription if it doesn't exist
        transcription = VideoTranscription(
            video_id=video_id,
            video_url=request.video_url,
            status=TranscriptionStatus.PENDING,  # Use enum value
        )
        db.add(transcription)
        await db.commit()

        # Start transcription process
        fetch_or_generate_transcript_with_whisper.delay(request.video_url)

        return {
            "status": "processing",
            "message": "Transcription started",
            "video_id": video_id,
        }
    except Exception as e:
        logger.error(f"Error starting transcription: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to start transcription process"
        )


@router.get("/status/{video_id}")
async def get_transcription_status(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(VideoTranscription).where(VideoTranscription.video_id == video_id)
        )
        transcription = result.scalars().first()
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")
        return {
            "status": transcription.status,
            "transcript": (
                transcription.transcript
                if transcription.status == TranscriptionStatus.COMPLETED
                else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcription status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch transcription status"
        )
