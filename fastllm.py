# fastllm.py
import os
from openai import OpenAI
from dotenv import load_dotenv

# ✅ Load .env variables
load_dotenv()

# ✅ Ensure keys are loaded
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE")

if not api_key or not base_url:
    raise ValueError("Missing OpenRouter key or base URL in .env")

# ✅ Initialize OpenAI client for OpenRouter
openai_client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

def fast_chat(prompt: str) -> str:
    try:
        response = openai_client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",  # or another fast model
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Fast model failed: {str(e)}"