"""Extended v2 architecture settings for production readiness.

This module defines configuration for the multi-agent, adversarially-hardened
pipeline addressing the Claude report findings.
"""

from pydantic import BaseModel, Field
from typing import List, Literal


class EmailParsingSettings(BaseModel):
    """Settings for RFC-compliant email parsing (Phase 1)."""
    
    strict_mime_parsing: bool = Field(
        default=True,
        description="Enforce strict RFC 2045-2049 MIME parsing",
    )
    preserve_attachments: bool = Field(
        default=False,
        description="Extract and redact PII from base64 attachments",
    )
    decode_before_extraction: bool = Field(
        default=True,
        description="Decode quoted-printable/base64 before entity extraction",
    )
    reencode_after_redaction: bool = Field(
        default=True,
        description="Re-encode to original format after redaction",
    )
    protect_mime_boundaries: bool = Field(
        default=True,
        description="Never redact MIME boundary strings",
    )


class NormalizationSettings(BaseModel):
    """Settings for adversarial normalization (Phase 2)."""
    
    unicode_normalization: Literal["NFC", "NFKC", "NFD", "NFKD"] = Field(
        default="NFKC",
        description="Unicode normalization form (NFKC recommended for adversarial robustness)",
    )
    enable_homoglyph_resolution: bool = Field(
        default=True,
        description="Map confusable characters (Cyrillic→Latin)",
    )
    enable_zero_width_removal: bool = Field(
        default=True,
        description="Remove U+200B, U+200C, U+200D, U+FEFF",
    )
    enable_html_entity_decode: bool = Field(
        default=True,
        description="Decode &#XXXX; and &lt; entities",
    )
    enable_space_normalization: bool = Field(
        default=True,
        description="Collapse multiple spaces, remove spaces in phone numbers",
    )
    enable_dot_normalization: bool = Field(
        default=True,
        description="john.doe → johndoe for fuzzy matching",
    )
    enable_hyphen_normalization: bool = Field(
        default=True,
        description="PAN-CARD → PANCARD for pattern matching",
    )


class HybridNERSettings(BaseModel):
    """Settings for hybrid rule+transformer NER (Phase 3)."""
    
    use_transformer_ner: bool = Field(
        default=True,
        description="Enable transformer-based NER (requires GPU or slow CPU inference)",
    )
    transformer_models: List[str] = Field(
        default=["xlm-roberta-base", "ai4bharat/indic-bert"],
        description="Transformer models to benchmark/use",
    )
    active_model: str = Field(
        default="xlm-roberta-base",
        description="Currently active transformer model",
    )
    hybrid_fusion_alpha: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Weight for rule-based confidence in fusion (1-alpha for transformer)",
    )
    rule_confidence_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for rule-only detections",
    )
    transformer_confidence_threshold: float = Field(
        default=0.72,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for transformer-only detections",
    )
    enable_trie_matching: bool = Field(
        default=True,
        description="Use trie structure for O(n) rule-based matching",
    )


class SchemaValidationSettings(BaseModel):
    """Settings for schema validation registry (Phase 3)."""
    
    enable_schema_validation: bool = Field(
        default=True,
        description="Validate all entities against schema registry",
    )
    enable_checksum_validation: bool = Field(
        default=True,
        description="Verify Verhoeff (Aadhaar), Luhn (credit cards) checksums",
    )
    strict_label_validation: bool = Field(
        default=True,
        description="Reject entities with ambiguous labels",
    )
    mutual_exclusion_enabled: bool = Field(
        default=True,
        description="Enforce mutual exclusion (Aadhaar XOR DATE_TIME)",
    )
    enable_rbi_registry_lookup: bool = Field(
        default=True,
        description="Validate IFSC codes against RBI bank code registry",
    )


class MultiAgentSettings(BaseModel):
    """Settings for multi-agent validation pipeline (Phase 3)."""
    
    enable_verifier_agent: bool = Field(
        default=True,
        description="Enable context cross-reference and FP filtering",
    )
    enable_auditor_agent: bool = Field(
        default=True,
        description="Enable schema validation and label-swap detection",
    )
    enable_policy_agent: bool = Field(
        default=True,
        description="Enable PDPB/Aadhaar/RBI compliance evaluation",
    )
    enable_composite_pii_detection: bool = Field(
        default=True,
        description="Detect quasi-identifiers (partial account + name + date)",
    )


class ComplianceSettings(BaseModel):
    """Settings for regulatory compliance (Phase 3)."""
    
    compliance_frameworks: List[str] = Field(
        default=["PDPB", "Aadhaar", "RBI"],
        description="Active compliance frameworks",
    )
    audit_logging_enabled: bool = Field(
        default=True,
        description="Log all entity detections with confidence scores",
    )
    generate_compliance_reports: bool = Field(
        default=True,
        description="Generate PDPB/Aadhaar/RBI compliance reports",
    )
    leakage_rate_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Maximum acceptable leakage rate (5% default, report had 48%)",
    )
    fail_on_compliance_violation: bool = Field(
        default=True,
        description="Fail pipeline if leakage exceeds threshold",
    )


class V2ArchitectureSettings(BaseModel):
    """Master configuration for v2 production-ready architecture.
    
    Addresses all critical findings from Claude report:
    - RFC-compliant email parsing (fixes 29% MIME corruption)
    - Adversarial normalization (fixes 96% bypass rate)
    - Hybrid NER (fixes 0.54 PERSON recall)
    - Schema validation (fixes label-swapping)
    - Multi-agent verification (enables audit trail)
    - Compliance reporting (PDPB/Aadhaar/RBI)
    """
    
    # Phase 1: Structural foundation
    email_parsing: EmailParsingSettings = Field(default_factory=EmailParsingSettings)
    
    # Phase 2: Adversarial hardening
    normalization: NormalizationSettings = Field(default_factory=NormalizationSettings)
    
    # Phase 3: NER & validation
    hybrid_ner: HybridNERSettings = Field(default_factory=HybridNERSettings)
    schema_validation: SchemaValidationSettings = Field(default_factory=SchemaValidationSettings)
    multi_agent: MultiAgentSettings = Field(default_factory=MultiAgentSettings)
    compliance: ComplianceSettings = Field(default_factory=ComplianceSettings)
    
    # Runtime safeguards (inherited from original V2RuntimeSettings)
    strict_mode: bool = Field(default=True)
    fail_closed: bool = Field(default=True)
    max_chunks_per_document: int = Field(default=5000, ge=1)
    max_entities_per_chunk: int = Field(default=500, ge=1)
    max_processing_seconds: int = Field(default=300, ge=1)
    redact_by_default_when_pii_present: bool = Field(default=True)
    
    # Legacy compatibility (for transition)
    use_legacy_agents: bool = Field(
        default=False,
        description="Use v1 agents (NOT recommended - for migration only)",
    )
