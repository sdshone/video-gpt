from fastapi import FastAPI, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routes import query, auth, transcript
from dotenv import load_dotenv
from db import init_db
import logging
from utils.cleanup import ResourceCleaner
import tempfile
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from datetime import datetime
from sqlalchemy import text
from db import engine

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.API_RATE_LIMIT]
)
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Remove trailing slash
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(query.router, prefix="/query")
app.include_router(auth.router, prefix="/auth")
app.include_router(transcript.router, prefix="/transcript")

# Load environment variables
load_dotenv()

# Initialize resource cleaner
temp_cleaner = ResourceCleaner(tempfile.gettempdir())

@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
        # Clean up any leftover temporary files
        await temp_cleaner.cleanup_temp_files()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    try:
        # Clean up temporary files
        await temp_cleaner.cleanup_temp_files()
        # Close database connections
        await engine.dispose()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Shutdown cleanup failed: {e}")

@app.get("/health")
async def health_check():
    try:
        # Check database connection
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
