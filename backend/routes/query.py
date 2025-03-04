import logging

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db import get_db
from models.query_interaction import QueryInteraction
from models.video_transcription import VideoTranscription
from services.auth import get_current_user
from services.gemini_client import get_gemini_response
from utils.embeddings import find_relevant_chunks

router = APIRouter()

logger = logging.getLogger(__name__)


# Define request model
class QueryRequest(BaseModel):
    video_id: str
    question: str


limiter = Limiter(key_func=get_remote_address)


@router.post("/ask-question")
@limiter.limit("5/minute")
async def ask_question(
    request: Request,  # Add this parameter for rate limiting
    query: QueryRequest,  # Rename from 'request' to 'query' to avoid conflict
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(VideoTranscription).where(
                VideoTranscription.video_id == query.video_id
            )
        )
        video = result.scalars().first()

        if not video or not video.chunks or not video.embeddings:
            raise HTTPException(
                status_code=404, detail="Transcript not found for the given video."
            )

        # Convert stored embeddings back to numpy arrays
        embeddings = [np.array(emb) for emb in video.embeddings]

        # Find relevant chunks for the query
        relevant_chunks = find_relevant_chunks(query.question, video.chunks, embeddings)

        # Construct context from relevant chunks
        context = "\n".join(relevant_chunks)

        # Get answer using Gemini
        response = await get_gemini_response(context, query.question)

        # Store the interaction without specifying the ID
        interaction = QueryInteraction(
            username=current_user,
            video_id=query.video_id,
            question=query.question,
            answer=response,
            context=context,
        )
        db.add(interaction)
        await db.commit()

        return {
            "answer": response,
            "context": relevant_chunks,  # Optionally return the used context
        }
    except Exception as e:
        logger.error(f"Error processing question for video {query.video_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process your question. Please try again later.",
        )


@router.get("/history/{video_id}")
async def get_query_history(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(QueryInteraction)
            .where(
                QueryInteraction.video_id == video_id,
                QueryInteraction.username == current_user,
            )
            .order_by(QueryInteraction.created_at.desc())
        )
        interactions = result.scalars().all()

        return [
            {
                "id": interaction.id,
                "question": interaction.question,
                "answer": interaction.answer,
                "created_at": interaction.created_at,
            }
            for interaction in interactions
        ]
    except Exception as e:
        logger.error(f"Error fetching history for video {video_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch query history")
