# fastllm.py
import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE")

if not api_key or not base_url:
    raise ValueError("Missing OpenRouter key or base URL in .env")

# Configure OpenAI client
openai.api_key = api_key
openai.api_base = base_url  # For OpenRouter or custom endpoint

def fast_chat(prompt: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Fast model failed: {str(e)}"