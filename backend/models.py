from pydantic import BaseModel
from typing import Optional, Dict, Any

class QueryRequest(BaseModel):
    query: str
    metadata: Optional[Dict[str, Any]] = None  # Enforce metadata to be a dict of str:str

    class Config:
        extra = "forbid"  # Disallow any unexpected fields in the payload


class QueryResponse(BaseModel):
    question: str
    structured_query: Dict
    final_answer: str
    matched_clause: str
    reason: str
    metadata: Optional[Dict[str, str]] = None
