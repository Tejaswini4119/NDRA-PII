from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any

# --- NSRL Rule Schemas ---

class RuleMeta(BaseModel):
    name: str
    description: str
    priority: int = 0
    tags: List[str] = []

class RuleCondition(BaseModel):
    type: str # e.g., "PII_MATCH"
    field: str # e.g., "type", "confidence"
    operator: str # e.g., "EQUALS", "GREATER_THAN"
    value: Any

class RuleActions(BaseModel):
    classification: str # e.g., "RESTRICTED"
    severity: str # "CRITICAL", "HIGH"...
    score: float
    justification: Optional[str] = None
    tags: List[str] = []

class NSRLRule(BaseModel):
    id: str
    version: str
    meta: RuleMeta
    conditions: List[RuleCondition]
    actions: RuleActions
