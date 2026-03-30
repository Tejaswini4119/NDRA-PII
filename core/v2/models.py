from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional


DecisionAction = Literal["Allow", "Redact", "Escalate", "Block", "Quarantine"]


class OrchestrationStepMetric(BaseModel):
    name: str
    elapsed_ms: int = Field(ge=0)


class PipelineContext(BaseModel):
    trace_id: str
    filename: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PipelineOutput(BaseModel):
    trace_id: str
    filename: str
    status: Literal["processed", "failed"]
    chunks_count: int
    pii_detected_count: int
    policy_decisions_count: int
    final_action: DecisionAction
    redacted_text_preview: Optional[str] = None
    step_metrics: List[OrchestrationStepMetric] = []
    diagnostics: Dict[str, str] = {}
