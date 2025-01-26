from sqlalchemy import Column, Integer, String, Text
from models import Base

class VideoTranscription(Base):
    __tablename__ = "video_transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, unique=True, nullable=False)
    video_url = Column(String, nullable=False)
    transcript = Column(Text, nullable=True)
    status = Column(String, default="pending")  # "pending", "completed", "error"
