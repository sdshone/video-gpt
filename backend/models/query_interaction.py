from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from models import Base

class QueryInteraction(Base):
    __tablename__ = "query_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)  # From JWT token
    video_id = Column(String, ForeignKey("video_transcriptions.video_id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    context = Column(Text, nullable=True)  # Store the chunks used
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 