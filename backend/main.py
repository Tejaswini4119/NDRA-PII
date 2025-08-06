from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from models import QueryRequest, QueryResponse
from ragqexec import run_pipeline  # You will patch this next
import os
from dotenv import load_dotenv

# Load API key from .env if exists
load_dotenv()
API_KEY = os.getenv("NDRA_API_KEY")

app = FastAPI()

@app.middleware("http")
async def verify_token(request: Request, call_next):
    if API_KEY:
        token = request.headers.get("Authorization")
        if token != f"Bearer {API_KEY}":
            return JSONResponse(status_code=403, content={"error": "Unauthorized"})
    return await call_next(request)

@app.post("/ndra/run", response_model=QueryResponse)
async def ndra_run(query_input: QueryRequest):
    try:
        result = run_pipeline(query_input.query, query_input.metadata)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")