
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import uuid

# --- Enums & Literals ---
PII_SEVERITY = Literal["Critical", "High", "Medium", "Low"]
DECISION_ACTION = Literal["Allow", "Redact", "Escalate", "Block", "Quarantine"]
PROCESSING_STATUS = Literal["queued", "processing", "completed", "failed"]

# --- 1. Document Schema ---
class DocumentMetadata(BaseModel):
    filename: str
    file_size_bytes: int
    mime_type: str
    sha256_hash: str
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    page_count: Optional[int] = None
    language: Optional[str] = "en"
    source_channel: Optional[str] = "api"

class NDRAMessage(BaseModel):
    """Base message for inter-agent communication."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace_id: str

# --- 2. Chunk Schema ---
class SemanticChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    processed_text: str
    original_text: str 
    page_number: int
    token_span: tuple[int, int]  # (start, end)
    bbox: Optional[List[float]] = None # [x1, y1, x2, y2]
    section_label: Optional[str] = None
    
# --- 3. PII Detection Schema (Presidio + Custom) ---
class LocationContext(BaseModel):
    page_number: int
    char_start_on_page: int
    char_end_on_page: int
    nearby_context: Optional[str] = None # Snippet around the PII

class DetectedPII(BaseModel):
    entity_type: str  # e.g., PHONE_NUMBER, IN_AADHAAR
    text_value: str   # The actual text detected
    start_index: int  # Relative to Chunk
    end_index: int    # Relative to Chunk
    score: float      # Confidence score
    source: str       # "Presidio", "NSRL", "Regex"
    metadata: Dict[str, Any] = {}
    location: Optional[LocationContext] = None # Detailed mapping

class ClassifiedChunk(SemanticChunk):
    """Chunk enriched with PII detections."""
    detected_entities: List[DetectedPII] = []
    pii_density_score: float = 0.0

# --- 4. Decision & Audit Schema ---
class AgentDecision(BaseModel):
    trace_id: str
    chunk_id: str
    agent_name: str
    action: DECISION_ACTION
    risk_score: float
    justification_trace: List[str] # Rule trace: "Rule A fired -> Risk High -> Policy Block"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GovernedChunk(ClassifiedChunk):
    """Final output chunk after policy enforcement."""
    redacted_text: str
    decision: AgentDecision

class RawChunk(BaseModel):
    """Intermediate chunk representation before semantic processing."""
    text: str
    page_number: int
    source_processed: bool = False
