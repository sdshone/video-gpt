from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import get_db
from models.video_transcription import VideoTranscription
from services.auth import get_current_user
from services.openai_client import get_openai_response
from pydantic import BaseModel

router = APIRouter()

# Define request model
class QueryRequest(BaseModel):
    video_id: str
    question: str

@router.post("/ask-question")
async def ask_question(query: QueryRequest, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    # Fetch transcript from DB
    result = await db.execute(
        select(VideoTranscription).where(VideoTranscription.video_id == query.video_id)
    )
    video = result.scalars().first()

    if not video or not video.transcript:
        return {"status": "error", "message": "Transcript not found for the given video."}
    # Send transcript and user question to OpenAI
    response = get_openai_response(video.transcript, query.question)
    return {"answer": response}
