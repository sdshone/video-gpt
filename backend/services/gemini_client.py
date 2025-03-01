import logging
from typing import Optional
import google.genai as genai
import backoff
from config import get_settings

settings = get_settings()
GOOGLE_API_KEY = settings.GOOGLE_API_KEY

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Configure the Gemini API
model = 'gemini-2.0-flash'
client = genai.Client(api_key=GOOGLE_API_KEY)
logger = logging.getLogger(__name__)

@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=3
)
async def get_gemini_response(context: str, question: str) -> Optional[str]:
    try:
        prompt = f"Video Transcript Context: {context}\n\nUser Question: {question}\n\nAnswer:"
        response = client.models.generate_content(
            model=model, contents=prompt
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise 