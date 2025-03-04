from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from models import Base


class QueryInteraction(Base):
    __tablename__ = "query_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)  # Changed from user_id
    video_id = Column(
        String, ForeignKey("video_transcriptions.video_id"), nullable=False
    )
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    context = Column(Text, nullable=True)  # Make context nullable
    created_at = Column(DateTime, default=datetime.utcnow)
