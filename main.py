
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import asyncio
import collections
import os
import time
import threading
import uuid
from typing import Dict, List, Optional

from prometheus_client import make_asgi_app, Counter

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

# ---------------------------------------------------------------------------
# Rate-limit middleware (per-IP sliding window, no external dependencies)
# ---------------------------------------------------------------------------

class _RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding-window rate limiter applied to /analyze/* endpoints.

    Each client IP is allowed at most ``requests_per_minute`` requests in any
    60-second rolling window.  Requests that exceed the limit receive HTTP 429.
    CORS preflight (OPTIONS) requests are exempt.  Rate limiting is disabled
    when ``requests_per_minute`` is 0.
    """

    def __init__(self, app, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.rpm = requests_per_minute
        self._window = 60.0
        # Per-IP deque of recent request timestamps (monotonic seconds)
        self._requests: Dict[str, collections.deque] = collections.defaultdict(collections.deque)
        self._lock = threading.Lock()

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit /analyze/* ; skip CORS preflight and disabled limiter
        if (
            self.rpm == 0
            or not request.url.path.startswith("/analyze")
            or request.method == "OPTIONS"
        ):
            return await call_next(request)

        client_ip = self._client_ip(request)
        now = time.monotonic()
        cutoff = now - self._window

        with self._lock:
            timestamps = self._requests[client_ip]
            # Evict entries outside the sliding window
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()
            if len(timestamps) >= self.rpm:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            f"Rate limit exceeded. "
                            f"Maximum {self.rpm} requests per minute per IP."
                        )
                    },
                )
            timestamps.append(now)

        return await call_next(request)


# Register middlewares.  In Starlette, the LAST-registered middleware is
# the outermost (first to receive requests).  Register CORS last so it
# is outermost and handles preflight before the rate limiter.
app.add_middleware(
    _RateLimitMiddleware,
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# ---------------------------------------------------------------------------
# API key authentication dependency
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _require_api_key(api_key: Optional[str] = Security(_api_key_header)) -> None:
    """FastAPI dependency that enforces the API key when one is configured.

    When ``settings.API_KEY`` is None or empty the dependency is a no-op,
    allowing unauthenticated access in development.  In production, set
    ``API_KEY`` in the environment and every /analyze/* and /audit/* request
    must include the ``X-API-Key`` header.
    """
    if settings.API_KEY and api_key != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Set the X-API-Key request header.",
            headers={"WWW-Authenticate": "ApiKey"},
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

class DocumentRisk(BaseModel):
    """Document-level risk escalation result from CONTEXT_MATCH rule evaluation."""
    escalated: bool
    risk_score: float
    severity: str
    rules_fired: List[str]
    justifications: List[str]

class AnalysisResult(BaseModel):
    filename: str
    status: str
    chunks_count: int
    pii_detected_count: int
    pii_details: List[PIISummary] = []
    policy_decisions: List[PolicyTrace] = []
    document_risk: Optional[DocumentRisk] = None
    trace_id: str

# --- Endpoints ---

@app.get("/")
def health_check():
    return {
        "system": "NDRA-PII",
        "status": "active",
        "agents": ["Audit", "Extractor", "Classifier", "Fusion", "Policy", "Redaction"]
    }

@app.post("/analyze/upload", response_model=AnalysisResult, dependencies=[Depends(_require_api_key)])
async def analyze_file_upload(file: UploadFile = File(...)):
    """
    Real-time Upload & Analysis.
    USER UPLOADS FILE -> SAVED -> EXTRACTED -> CLASSIFIED -> RESULT
    """
    trace_id = str(uuid.uuid4())
    audit_agent.log_event("UPLOAD_RECEIVED", {"filename": file.filename, "trace_id": trace_id})

    # --- Input validation ---
    # 1. MIME-type whitelist
    content_type = file.content_type or ""
    if settings.ALLOWED_UPLOAD_MIMES and content_type not in settings.ALLOWED_UPLOAD_MIMES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: '{content_type}'. Allowed: {settings.ALLOWED_UPLOAD_MIMES}"
        )

    # 1. Save File Locally
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        # Use a safe filename derived only from the trace_id to avoid path traversal
        safe_name = os.path.basename(file.filename or "upload")
        file_location = os.path.join(settings.UPLOAD_DIR, f"{trace_id}_{safe_name}")

        # 2. Stream to disk while enforcing size limit
        bytes_written = 0
        with open(file_location, "wb") as buffer:
            while True:
                chunk = await file.read(65536)  # 64 KiB read chunks
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > settings.MAX_UPLOAD_BYTES:
                    buffer.close()
                    os.remove(file_location)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_BYTES} bytes."
                    )
                buffer.write(chunk)

        return await asyncio.to_thread(_run_pipeline, file_location, file.filename, trace_id)

    except HTTPException:
        raise
    except Exception as e:
        audit_agent.log_event("UPLOAD_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/path", response_model=AnalysisResult, dependencies=[Depends(_require_api_key)])
async def analyze_local_path(file_path: str):
    """
    Analyze a file already on the server/local disk.
    Only permitted when ALLOWED_PATH_PREFIXES is configured and the requested
    path falls within one of those prefixes.  The endpoint is disabled by
    default (empty ALLOWED_PATH_PREFIXES) to prevent arbitrary file-read.
    """
    # Disabled when no prefixes are configured
    if not settings.ALLOWED_PATH_PREFIXES:
        raise HTTPException(
            status_code=403,
            detail="The /analyze/path endpoint is disabled in this deployment."
        )

    # Resolve to an absolute, canonical path to defeat path-traversal attempts
    resolved = os.path.realpath(os.path.abspath(file_path))

    # Verify the path is within one of the allowed prefixes
    if not any(resolved.startswith(os.path.realpath(prefix)) for prefix in settings.ALLOWED_PATH_PREFIXES):
        raise HTTPException(
            status_code=403,
            detail="Access to the requested path is not permitted."
        )

    if not os.path.exists(resolved):
        raise HTTPException(status_code=404, detail="File not found")

    trace_id = str(uuid.uuid4())
    return await asyncio.to_thread(_run_pipeline, resolved, os.path.basename(resolved), trace_id)

@app.get("/audit/verify", dependencies=[Depends(_require_api_key)])
def audit_verify():
    """Verify the integrity of the tamper-evident audit log hash chain.

    Walks every entry in the audit log, recomputes each SHA-256 hash, and
    confirms that the ``prev_hash`` field in each entry correctly links to the
    hash of the preceding entry.  Returns the verification result without
    exposing any audit log content.
    """
    result = audit_agent.verify_chain()
    if not result["valid"]:
        # Return 409 Conflict to signal chain corruption — callers should
        # treat this as a security incident requiring investigation.
        raise HTTPException(
            status_code=409,
            detail=result,
        )
    return result

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
        
        # 5. Document-level escalation evaluation (CONTEXT_MATCH rules)
        # Runs after all per-chunk governance so the full PII inventory is known.
        doc_esc = policy_agent.evaluate_document(fused_chunks, trace_id=trace_id)
        document_risk = DocumentRisk(
            escalated=doc_esc["escalated"],
            risk_score=doc_esc["risk_score"],
            severity=doc_esc["severity"],
            rules_fired=doc_esc["rules_fired"],
            justifications=doc_esc["justifications"],
        )

        # 6. Audit
        audit_agent.log_event("ANALYSIS_COMPLETE", {
            "file": filename,
            "pii_count": total_pii,
            "decisions": len(policy_traces),
            "doc_escalated": doc_esc["escalated"],
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
            document_risk=document_risk,
            trace_id=trace_id
        )
        
    except HTTPException:
        # Re-raise FastAPI/HTTP errors without wrapping them in a 500 — they
        # carry a meaningful status code (e.g. 404, 403) that must reach the caller.
        raise
    except Exception as e:
        PII_FILES_PROCESSED.labels(status="failed").inc()
        audit_agent.log_event("PIPELINE_ERROR", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Pipeline Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
