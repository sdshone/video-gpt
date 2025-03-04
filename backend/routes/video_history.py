from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db import async_session
from models.query_interaction import QueryInteraction
from models.user import User
from models.video_transcription import VideoTranscription
from services.auth import get_current_user

router = APIRouter()


class VideoHistoryResponse(BaseModel):
    video_id: str
    video_title: Optional[str] = "Untitled Video"
    last_interaction: Optional[datetime] = None
    thumbnail_url: Optional[str] = ""

    class Config:
        from_attributes = True


class QueryHistoryResponse(BaseModel):
    question: str
    answer: str
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("/videos/history", response_model=List[VideoHistoryResponse])
async def get_video_history(current_user: str = Depends(get_current_user)):
    """Get all videos that the user has interacted with"""
    try:
        async with async_session() as db:
            # First, get all video IDs the user has interacted with
            query = (
                select(
                    VideoTranscription.video_id,
                    VideoTranscription.title,
                    VideoTranscription.thumbnail_url,
                    func.max(QueryInteraction.created_at).label("last_interaction"),
                )
                .select_from(QueryInteraction)
                .join(
                    VideoTranscription,
                    VideoTranscription.video_id == QueryInteraction.video_id,
                )
                .where(QueryInteraction.username == current_user)
                .group_by(
                    VideoTranscription.video_id,
                    VideoTranscription.title,
                    VideoTranscription.thumbnail_url,
                )
                .order_by(desc("last_interaction"))
            )

            result = await db.execute(query)
            videos = result.all()

            return [
                VideoHistoryResponse(
                    video_id=video.video_id,
                    video_title=video.title or "Untitled Video",
                    last_interaction=video.last_interaction,
                    thumbnail_url=video.thumbnail_url or "",
                )
                for video in videos
            ]
    except Exception as e:
        print(f"Error in get_video_history: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch video history: {str(e)}"
        )


@router.get("/videos/{video_id}/queries", response_model=List[QueryHistoryResponse])
async def get_video_queries(
    video_id: str, current_user: str = Depends(get_current_user)
):
    """Get all queries for a specific video"""
    try:
        async with async_session() as db:
            # Get all queries for this video from this user
            query = (
                select(QueryInteraction)
                .where(
                    QueryInteraction.video_id == video_id,
                    QueryInteraction.username == current_user,
                )
                .order_by(desc(QueryInteraction.created_at))
            )

            result = await db.execute(query)
            queries = result.scalars().all()

            return [
                QueryHistoryResponse(
                    question=query.question,
                    answer=query.answer,
                    timestamp=query.created_at,
                )
                for query in queries
            ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch query history: {str(e)}"
        )
