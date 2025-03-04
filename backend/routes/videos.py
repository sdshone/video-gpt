import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.video_transcription import VideoTranscription
from services.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{video_id}")
async def get_video_details(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(VideoTranscription).where(VideoTranscription.video_id == video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        return {
            "video_id": video.video_id,
            "video_title": video.title,
            "thumbnail_url": video.thumbnail_url,
            "created_at": video.created_at,
            "status": video.status,
        }
    except Exception as e:
        logger.error(f"Error fetching video details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch video details")
