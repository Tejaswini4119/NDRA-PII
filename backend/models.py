from pydantic import BaseModel
from typing import Optional, Dict

class QueryRequest(BaseModel):
    query: str
    metadata: Optional[Dict] = None

class QueryResponse(BaseModel):
    question: str
    structured_query: Dict
    final_answer: str
    matched_clause: str
    reason: str
    metadata: Optional[Dict] = None