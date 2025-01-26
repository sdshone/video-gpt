
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from tasks.video_processor import fetch_or_generate_transcript_with_whisper
from pydantic import BaseModel
from models.video_transcription import VideoTranscription

from db import get_db, init_db

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/")
async def root():
    return {"message": "Welcome to the Video Query System!"}

# @app.get("/test-db")
# async def test_db(session: AsyncSession = Depends(get_db)):
#     try:
#         # Run a raw SQL query to check the connection
#         result = await session.execute(text("SELECT 1"))
#         # Fetch the result
#         return {"status": "success", "result": result.scalar()}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}


class VideoRequest(BaseModel):
    video_url: str


# from fastapi import FastAPI, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from db import get_db
# from tasks.video_processor import fetch_or_generate_transcript_with_whisper
# from schemas import VideoRequest  # Assuming this is the Pydantic model

# app = FastAPI()

@app.post("/transcribe-or-fetch")
async def transcribe_or_fetch(request: VideoRequest, db: AsyncSession = Depends(get_db)):
    """
    Handles requests to fetch or transcribe YouTube videos.
    :param request: Contains the video_url.
    :param db: Database session provided via dependency injection.
    """
    try:
        # Extract video_url from the request
        video_url = request.video_url

        # Call the transcription function
        result = await fetch_or_generate_transcript_with_whisper(video_url, db)

        # Handle errors in the transcription process
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except Exception as e:
        # Catch any unexpected exceptions and return a 500 error
        raise HTTPException(status_code=500, detail=str(e))
