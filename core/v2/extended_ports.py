"""Extended port definitions for v2 architecture.

Adds new ports required by Claude report recommendations:
- EmailParserPort: RFC-compliant MIME parsing
- NormalizerPort: Adversarial text normalization
- VerifierPort: Contextual validation
- AuditorPort: Schema validation
- CompliancePort: Regulatory compliance evaluation
"""

from typing import List, Protocol, Dict, Any
from dataclasses import dataclass
from email.message import Message


# ============================================================================
# Phase 1: Email Parsing
# ============================================================================

@dataclass
class ParsedEmail:
    """RFC-compliant parsed email structure."""
    
    headers: Dict[str, str]
    """Email headers (From, To, Subject, etc.)"""
    
    body_text: str
    """Plain text body content (decoded from quoted-printable/base64)"""
    
    body_html: str | None
    """HTML body content if present"""
    
    attachments: List[Dict[str, Any]]
    """List of attachments with metadata"""
    
    mime_boundaries: List[str]
    """MIME boundary strings to protect during redaction"""
    
    original_encoding: str
    """Original character encoding (for re-encoding after redaction)"""
    
    raw_message: Message
    """Original email.message.Message object for reconstruction"""


class EmailParserPort(Protocol):
    """Port for RFC 5322/2045-2049 compliant email parsing.
    
    Addresses Claude report finding: 29% MIME corruption rate.
    """
    
    def parse(self, raw_email: bytes) -> ParsedEmail:
        """Parse raw email bytes into structured components.
        
        Args:
            raw_email: Raw .eml file as bytes
            
        Returns:
            ParsedEmail with decoded headers, body, attachments
            
        Raises:
            EmailParsingError: If email is malformed
        """
        ...
    
    def reconstruct(self, parsed: ParsedEmail, redacted_text: str) -> bytes:
        """Reconstruct email with redacted text, preserving structure.
        
        Args:
            parsed: Original ParsedEmail
            redacted_text: Redacted body text
            
        Returns:
            Reconstructed .eml as bytes with proper MIME encoding
        """
        ...


# ============================================================================
# Phase 2: Adversarial Normalization
# ============================================================================

@dataclass
class NormalizedText:
    """Text with adversarial normalization applied."""
    
    normalized: str
    """Normalized text for entity extraction"""
    
    original: str
    """Original text before normalization"""
    
    transform_map: Dict[int, int]
    """Mapping from normalized char indices to original char indices"""


class NormalizerPort(Protocol):
    """Port for adversarial text normalization.
    
    Addresses Claude report finding: 96% adversarial bypass rate.
    """
    
    def normalize(self, text: str) -> NormalizedText:
        """Apply adversarial normalization transforms.
        
        Transformations (in order):
        1. Unicode NFC/NFKC normalization
        2. Homoglyph resolution (Cyrillic→Latin)
        3. Zero-width character removal (U+200B, U+200C, U+200D, U+FEFF)
        4. HTML entity decoding (&#XXXX;, &lt;)
        5. Space/dot/hyphen normalization
        
        Args:
            text: Original text
            
        Returns:
            NormalizedText with transform map for span reconstruction
        """
        ...
    
    def denormalize_spans(
        self, 
        spans: List[tuple[int, int]], 
        normalized: NormalizedText
    ) -> List[tuple[int, int]]:
        """Map entity spans from normalized text back to original.
        
        Args:
            spans: List of (start, end) spans in normalized text
            normalized: NormalizedText with transform map
            
        Returns:
            Spans mapped to original text indices
        """
        ...


# ============================================================================
# Phase 3: Hybrid NER
# ============================================================================

@dataclass
class EntitySpan:
    """Detected entity span with metadata."""
    
    start: int
    """Start character index"""
    
    end: int
    """End character index"""
    
    text: str
    """Extracted text"""
    
    label: str
    """Entity label (PERSON, IN_AADHAAR, etc.)"""
    
    confidence: float
    """Confidence score [0.0, 1.0]"""
    
    source: str
    """Detection source: 'rule', 'transformer', 'fused'"""
    
    metadata: Dict[str, Any]
    """Additional metadata (pattern name, model layer, etc.)"""


class HybridExtractorPort(Protocol):
    """Extended extractor with dual-path NER.
    
    Addresses Claude report finding: 0.54 PERSON recall in free text.
    """
    
    def extract_rules(self, text: str) -> List[EntitySpan]:
        """High-precision rule-based extraction.
        
        Uses trie structure for O(n) pattern matching with priority ordering
        and mutual exclusion constraints.
        
        Args:
            text: Normalized text
            
        Returns:
            Entity spans with confidence ≥ 0.85
        """
        ...
    
    def extract_transformer(self, text: str) -> List[EntitySpan]:
        """High-recall transformer NER.
        
        Uses fine-tuned XLM-RoBERTa or IndicBERT for contextual extraction.
        
        Args:
            text: Normalized text
            
        Returns:
            Entity spans with confidence ≥ 0.72
        """
        ...
    
    def fuse_extractions(
        self, 
        rule_spans: List[EntitySpan], 
        transformer_spans: List[EntitySpan],
        alpha: float = 0.6
    ) -> List[EntitySpan]:
        """α-weighted confidence fusion.
        
        For overlapping spans: c_fused = α*c_rule + (1-α)*c_transformer
        
        Args:
            rule_spans: Rule-based detections
            transformer_spans: Transformer detections
            alpha: Weight for rule-based confidence
            
        Returns:
            Fused entity spans with source='fused'
        """
        ...


# ============================================================================
# Phase 3: Validation Agents
# ============================================================================

@dataclass
class ValidationResult:
    """Result of entity validation."""
    
    valid: bool
    """Whether entity passed validation"""
    
    errors: List[str]
    """Validation errors if invalid"""
    
    warnings: List[str]
    """Non-fatal warnings"""


class VerifierPort(Protocol):
    """Port for contextual entity verification.
    
    Addresses Claude report finding: No co-reference resolution.
    """
    
    def verify(self, spans: List[EntitySpan], text: str) -> List[EntitySpan]:
        """Cross-reference spans against contextual evidence.
        
        Checks:
        - Co-reference resolution (name abbreviations)
        - Entity consistency (same entity, same label)
        - False positive filtering (ORG name vs PERSON)
        
        Args:
            spans: Detected entity spans
            text: Full document text
            
        Returns:
            Verified spans (FPs removed, labels corrected)
        """
        ...


@dataclass
class SchemaValidationRule:
    """Schema validation predicate."""
    
    label: str
    """Entity label this rule applies to"""
    
    validator: str
    """Validator name (e.g., 'verhoeff_checksum', 'pan_format')"""
    
    error_message: str
    """Error message if validation fails"""


class SchemaRegistry:
    """Registry of validation rules for each entity class.
    
    Examples:
    - IN_AADHAAR: 12-digit + Verhoeff checksum + not-a-date
    - IN_PAN: [A-Z]{5}[0-9]{4}[A-Z]{1} format
    - IN_IFSC: [A-Z]{4}0[A-Z0-9]{6} + RBI bank code registry
    """
    
    rules: Dict[str, List[SchemaValidationRule]]


class AuditorPort(Protocol):
    """Port for schema validation and label consistency.
    
    Addresses Claude report finding: Aadhaar→DATE_TIME label-swapping.
    """
    
    def audit(
        self, 
        spans: List[EntitySpan], 
        schema: SchemaRegistry
    ) -> List[EntitySpan]:
        """Validate all labels against schema registry.
        
        Checks:
        - Checksum validation (Verhoeff, Luhn)
        - Format validation (regex, length)
        - Mutual exclusion (Aadhaar XOR DATE_TIME)
        - Registry lookup (RBI bank codes for IFSC)
        
        Args:
            spans: Verified entity spans
            schema: Schema validation registry
            
        Returns:
            Audited spans (invalid entities removed/relabeled)
        """
        ...
    
    def detect_label_swaps(
        self, 
        spans: List[EntitySpan]
    ) -> List[Dict[str, Any]]:
        """Detect common label-swapping errors.
        
        Returns:
            List of detected label-swap issues with corrections
        """
        ...


# ============================================================================
# Compliance & Reporting
# ============================================================================

@dataclass
class ComplianceReport:
    """Regulatory compliance report."""
    
    framework: str
    """Compliance framework (PDPB, Aadhaar, RBI)"""
    
    leakage_rate: float
    """Overall PII leakage rate [0.0, 1.0]"""
    
    entity_leakage: Dict[str, float]
    """Per-entity leakage rates"""
    
    violations: List[str]
    """Compliance violations detected"""
    
    audit_trail: List[Dict[str, Any]]
    """Detailed audit log of all decisions"""
    
    passed: bool
    """Whether document passed compliance check"""


class CompliancePort(Protocol):
    """Port for regulatory compliance evaluation.
    
    Addresses Claude report finding: Unfalsifiable compliance claims.
    """
    
    def evaluate_compliance(
        self, 
        original_text: str,
        redacted_text: str,
        detected_entities: List[EntitySpan],
        frameworks: List[str]
    ) -> List[ComplianceReport]:
        """Evaluate compliance for specified frameworks.
        
        Args:
            original_text: Original document text
            redacted_text: Redacted document text
            detected_entities: All detected entities (including missed ones)
            frameworks: List of frameworks to evaluate (PDPB, Aadhaar, RBI)
            
        Returns:
            Compliance reports for each framework
        """
        ...
    
    def calculate_leakage_rate(
        self, 
        expected_entities: List[EntitySpan],
        detected_entities: List[EntitySpan]
    ) -> float:
        """Calculate PII leakage rate.
        
        Leakage = (expected - detected) / expected
        
        Claude report baseline: 0.48 (48% leakage)
        Production target: <0.05 (5% leakage)
        
        Args:
            expected_entities: Ground truth entities (for testing)
            detected_entities: Actually detected entities
            
        Returns:
            Leakage rate [0.0, 1.0]
        """
        ...
