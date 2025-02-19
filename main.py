
from fastapi import FastAPI
from routes import query, auth, transcript
from dotenv import load_dotenv
from db import init_db

app = FastAPI()
app.include_router(query.router, prefix="/query")
app.include_router(auth.router, prefix="/auth")
app.include_router(transcript.router, prefix="/transcript")

# Load environment variables
load_dotenv()


@app.on_event("startup")
async def on_startup():
    await init_db()
