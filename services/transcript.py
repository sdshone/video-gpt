from sqlalchemy.orm import Session
from models.video_transcription import VideoTranscription

def get_transcript_by_video_id(db: Session, video_id: str):
    return db.query(VideoTranscription).filter(VideoTranscription.video_id == video_id).first()
