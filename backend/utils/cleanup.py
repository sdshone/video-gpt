import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ResourceCleaner:
    def __init__(self, temp_dir: str, max_age_hours: int = 24):
        self.temp_dir = temp_dir
        self.max_age_hours = max_age_hours

    async def cleanup_temp_files(self):
        """Clean up temporary files older than max_age_hours."""
        try:
            now = datetime.now()
            for filename in os.listdir(self.temp_dir):
                filepath = os.path.join(self.temp_dir, filename)
                file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                if now - file_modified > timedelta(hours=self.max_age_hours):
                    try:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old temp file: {filepath}")
                    except OSError as e:
                        logger.error(f"Failed to delete {filepath}: {e}")
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}") 