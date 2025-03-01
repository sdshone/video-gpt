import re
from sqlalchemy import Column, Integer, String, Text, JSON, CheckConstraint
from models import Base

class VideoTranscription(Base):
    __tablename__ = "video_transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, unique=True, nullable=False)
    video_url = Column(String, nullable=False)
    transcript = Column(Text, nullable=True)
    chunks = Column(JSON, nullable=True)  # Store transcript chunks
    embeddings = Column(JSON, nullable=True)  # Store embeddings as JSON
    status = Column(String, default="pending")  # "pending", "completed", "error"

    # Only keep the status constraint
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'error')",
            name='valid_status'
        ),
    )

    @staticmethod
    def validate_youtube_url(url: str) -> bool:
        pattern = r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+$'
        return bool(re.match(pattern, url))