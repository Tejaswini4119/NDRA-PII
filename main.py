
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
import uuid
from typing import List, Optional

from prometheus_client import make_asgi_app, Counter

# Core Agents
from agents.audit import AuditAgent
# Core Agents
from agents.audit import AuditAgent
from agents.extractor import ExtractorAgent
from agents.classifier import ClassifierAgent
from agents.fusion_agent import FusionAgent
from agents.policy_agent import PolicyAgent
from agents.redaction_agent import RedactionAgent
from config.settings import settings

# Initialize Agents
audit_agent = AuditAgent()
extractor = ExtractorAgent()
classifier = ClassifierAgent()
fusion_agent = FusionAgent()
policy_agent = PolicyAgent()
redaction_agent = RedactionAgent()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Neuro-Semantic Distributed Risk Analysis for Personally Identifiable Information (NDRA-PII)"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Prometheus Metrics ---
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

PII_FILES_PROCESSED = Counter("ndrapii_files_processed_total", "Total documents processed", ["status"])
PII_POLICY_ACTIONS = Counter("ndrapii_policy_actions_total", "Actions taken by Policy Agent", ["action", "entity_type"])

# --- Schemas ---
class PIISummary(BaseModel):
    entity_type: str
    text_preview: str
    score: float
    location_str: str

class PolicyTrace(BaseModel):
    chunk_id: str
    action: str
    risk_score: float
    details: List[str]

class AnalysisResult(BaseModel):
    filename: str
    status: str
    chunks_count: int
    pii_detected_count: int
    pii_details: List[PIISummary] = []
    policy_decisions: List[PolicyTrace] = []
    trace_id: str

# --- Endpoints ---

@app.get("/")
def health_check():
    return {
        "system": "NDRA-PII",
        "status": "active",
        "agents": ["Audit", "Extractor", "Classifier", "Fusion", "Policy", "Redaction"]
    }

@app.post("/analyze/upload", response_model=AnalysisResult)
async def analyze_file_upload(file: UploadFile = File(...)):
    """
    Real-time Upload & Analysis.
    USER UPLOADS FILE -> SAVED -> EXTRACTED -> CLASSIFIED -> RESULT
    """
    trace_id = str(uuid.uuid4())
    audit_agent.log_event("UPLOAD_RECEIVED", {"filename": file.filename, "trace_id": trace_id})
    
    # 1. Save File Locally
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_location = f"{settings.UPLOAD_DIR}/{trace_id}_{file.filename}"
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return _run_pipeline(file_location, file.filename, trace_id)
        
    except Exception as e:
        audit_agent.log_event("UPLOAD_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/path", response_model=AnalysisResult)
async def analyze_local_path(file_path: str):
    """
    Analyze a file already on the server/local disk (Test Case Use).
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    trace_id = str(uuid.uuid4())
    return _run_pipeline(file_path, os.path.basename(file_path), trace_id)

def _run_pipeline(file_path: str, filename: str, trace_id: str) -> AnalysisResult:
    """Helper to run Extractor -> Classifier -> Fusion -> Policy -> Redaction pipeline."""
    try:
        # 1. Extraction
        chunks = extractor.process(file_path)
        
        # 2. Classification & Fusion
        classified_chunks = []
        for chunk in chunks:
            classified = classifier.process(chunk)
            # Apply Intra-Chunk Fusion
            classified = fusion_agent.fuse_chunk(classified)
            classified_chunks.append(classified)
            
        # 3. Cross-Chunk Fusion
        fused_chunks = fusion_agent.fuse_cross_chunks(classified_chunks)
        
        # 4. Governance & Redaction
        pii_summaries = []
        policy_traces = []
        total_pii = 0
        
        for final_chunk in fused_chunks:
            # Apply Policy
            governed = policy_agent.evaluate_chunk(final_chunk, trace_id)
            
            # Apply Redaction
            redacted_chunk = redaction_agent.redact(governed)
            
            # Collect Policy Decisions
            if redacted_chunk.decision.action != "Allow" or redacted_chunk.decision.risk_score > 0:
                 policy_traces.append(PolicyTrace(
                     chunk_id=redacted_chunk.chunk_id,
                     action=redacted_chunk.decision.action,
                     risk_score=redacted_chunk.decision.risk_score,
                     details=redacted_chunk.decision.justification_trace
                 ))

            if redacted_chunk.detected_entities:
                total_pii += len(redacted_chunk.detected_entities)
                for pii in redacted_chunk.detected_entities:
                    # Export Metric: Policy decision per actual entity
                    PII_POLICY_ACTIONS.labels(
                        action=redacted_chunk.decision.action, 
                        entity_type=pii.entity_type
                    ).inc()

                    # Format Location
                    loc_str = "N/A"
                    if pii.location:
                         loc_str = f"Page {pii.location.page_number} [{pii.location.char_start_on_page}:{pii.location.char_end_on_page}]"
                    
                    # Decide on text preview
                    # If Action was Redact, we should probably mask the preview too for safety
                    preview = pii.text_value
                    if redacted_chunk.decision.action == "Redact":
                        preview = f"[{pii.entity_type}]"

                    pii_summaries.append(PIISummary(
                        entity_type=pii.entity_type,
                        text_preview=preview,
                        score=pii.score,
                        location_str=loc_str
                    ))
        
        # 3. Audit
        audit_agent.log_event("ANALYSIS_COMPLETE", {
            "file": filename,
            "pii_count": total_pii,
            "decisions": len(policy_traces),
            "trace_id": trace_id
        })
        
        PII_FILES_PROCESSED.labels(status="success").inc()
        
        return AnalysisResult(
            filename=filename,
            status="processed",
            chunks_count=len(chunks),
            pii_detected_count=total_pii,
            pii_details=pii_summaries,
            policy_decisions=policy_traces,
            trace_id=trace_id
        )
        
    except Exception as e:
        PII_FILES_PROCESSED.labels(status="failed").inc()
        audit_agent.log_event("PIPELINE_ERROR", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Pipeline Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
