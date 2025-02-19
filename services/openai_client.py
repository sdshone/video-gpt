import requests
import json
import os


OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY") 
def get_openai_response(transcript: str, question: str):
    prompt = f"Video Transcript: {transcript[:200]}\n\nUser Question: {question}\n\nAnswer:"

    response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
        # "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
        # "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
    },
    data=json.dumps({
        "model": "deepseek/deepseek-r1:free", # Optional
        "messages": [
        {
            "role": "user",
            "content": prompt,
        }
        ]
        
    })
    )
    return response.json()["choices"][0]["message"]["content"]