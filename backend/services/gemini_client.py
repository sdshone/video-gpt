import logging
from typing import Optional

import backoff
import google.genai as genai

from config import get_settings

settings = get_settings()
GOOGLE_API_KEY = settings.GOOGLE_API_KEY

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Configure the Gemini API
model = "gemini-2.0-flash"
client = genai.Client(api_key=GOOGLE_API_KEY)
logger = logging.getLogger(__name__)


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
async def get_gemini_response(context: str, question: str) -> Optional[str]:
    try:
        prompt = f"""You are an AI assistant helping users understand video content. Answer the following question based on the provided video transcript excerpt.

        Context from Video Transcript:
        {context}

        Question: {question}

        Instructions:
        1. Answer based ONLY on the information provided in the transcript context
        2. If the answer cannot be found in the context, say "I cannot answer this based on the available transcript"
        3. Keep the answer focused and relevant to the question
        4. Use clear, natural language
        5. If appropriate, cite specific parts of the transcript"""

        response = client.models.generate_content(model=model, contents=prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise
