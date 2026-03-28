from pydantic import BaseModel, Field


class V2RuntimeSettings(BaseModel):
    """Runtime safety controls for the v2 orchestrator."""

    strict_mode: bool = Field(default=True)
    fail_closed: bool = Field(default=True)
    max_chunks_per_document: int = Field(default=5000, ge=1)
    max_entities_per_chunk: int = Field(default=500, ge=1)
    max_processing_seconds: int = Field(default=300, ge=1)
    redact_by_default_when_pii_present: bool = Field(default=True)
