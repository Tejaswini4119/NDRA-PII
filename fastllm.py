import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE")  # e.g., https://openrouter.ai/api/v1

if not api_key:
    raise ValueError("Missing API key in .env")
if not base_url:
    raise ValueError("Missing API base URL in .env")

# Configure OpenAI client for OpenRouter
openai.api_key = api_key
openai.api_base = base_url  # ✅ exact URL

def fast_chat(prompt: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="mistralai/mistral-7b-instruct:free",  # ✅ real model ID
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"⚠️ Fast model failed: {str(e)}"
