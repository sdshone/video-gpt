import re
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, CheckConstraint, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, Text

from models import Base


class TranscriptionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class VideoTranscription(Base):
    __tablename__ = "video_transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, unique=True, nullable=False)
    video_url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    chunks = Column(JSON, nullable=True)  # Store transcript chunks
    embeddings = Column(JSON, nullable=True)  # Store embeddings as JSON
    status = Column(SQLEnum(TranscriptionStatus), default=TranscriptionStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Only keep the status constraint
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'ERROR')", name="valid_status"
        ),
    )

    @staticmethod
    def validate_youtube_url(url: str) -> bool:
        pattern = r"^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+$"
        return bool(re.match(pattern, url))
