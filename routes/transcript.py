from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from db import get_db
from services.auth import get_current_user
from tasks.video_processor import fetch_or_generate_transcript_with_whisper
from sqlalchemy.ext.asyncio import AsyncSession
from celery.result import AsyncResult
from tasks.video_processor import celery_app
from models.video_transcription import VideoTranscription
router = APIRouter()

class VideoRequest(BaseModel):
    video_url: str

@router.post("/transcribe-or-fetch")
async def transcribe_or_fetch(
    request: VideoRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(get_current_user)
):
    try:
        video_url = request.video_url

        # Check if the transcript already exists for this user
        result = await db.execute(
            select(VideoTranscription).where(
                VideoTranscription.video_url == video_url,
            )
        )
        existing_transcript = result.scalars().first()

        if existing_transcript:
            return {"task_id": existing_transcript.task_id, "status": existing_transcript.status}

        # If not found, create a new task
        task = fetch_or_generate_transcript_with_whisper.apply_async(args=[video_url, db])

        new_transcript = VideoTranscription(
            video_url=video_url,
        )
        db.add(new_transcript)
        await db.commit()

        return {"task_id": task.id, "status": "in progress"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/task-status/{task_id}")
def task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.state == "PENDING":
        return {"task_id": task_id, "status": "pending"}
    elif task_result.state == "SUCCESS":
        return {"task_id": task_id, "status": "completed", "result": task_result.result}
    elif task_result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(task_result.result)}
    return {"task_id": task_id, "status": task_result.state}
