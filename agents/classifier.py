
from typing import List, Dict, Any
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerResult
from agents.base import NDRAAgent
from schemas.core_models import SemanticChunk, ClassifiedChunk, DetectedPII, PII_SEVERITY, LocationContext

class ClassifierAgent(NDRAAgent):
    """
    Phase 3: PII Detection using Microsoft Presidio + Custom Recognizers.
    Capabilities:
    - Standard Entities: PERSON, PHONE_NUMBER, EMAIL_ADDRESS, CREDIT_CARD, etc.
    - Custom Entities: AADHAAR_IN, PAN_IN.
    - Confidence Scoring
    """
    
    def __init__(self):
        super().__init__("ClassifierAgent")
        
        # Initialize Presidio
        # In a real setup, we might configure a specific NLP engine (Spacy/Transformers)
        self.analyzer = AnalyzerEngine() 
        
        # Add Custom Recognizers
        self._add_aadhaar_recognizer()
        self._add_pan_recognizer()

    def process(self, chunk: SemanticChunk, context: Dict[str, Any] = None) -> ClassifiedChunk:
        """
        Analyze a SemanticChunk for PII.
        """
        # 1. Analyze Text
        results = self.analyzer.analyze(
            text=chunk.processed_text,
            language="en",
            return_decision_process=True
        )
        
        # 2. Map Results to Schema
        detected_pii_list = []
        for res in results:
            # Extract actual text value using span
            text_val = chunk.processed_text[res.start:res.end]
            
            # Calculate Absolute Location on Page
            # chunk.token_span is (start, end) on the page
            page_offset_start = chunk.token_span[0] if chunk.token_span else 0
            abs_start = page_offset_start + res.start
            abs_end = page_offset_start + res.end
            
            loc = LocationContext(
                page_number=chunk.page_number,
                char_start_on_page=abs_start,
                char_end_on_page=abs_end,
                nearby_context=chunk.processed_text[max(0, res.start-20):min(len(chunk.processed_text), res.end+20)]
            )
            
            detected = DetectedPII(
                entity_type=res.entity_type,
                text_value=text_val,
                start_index=res.start,
                end_index=res.end,
                score=res.score,
                source="Presidio",
                location=loc
            )
            detected_pii_list.append(detected)
            
        # 3. Create Output
        classified = ClassifiedChunk(
            **chunk.dict(),
            detected_entities=detected_pii_list,
            pii_density_score=len(detected_pii_list) / max(1, len(chunk.processed_text.split())) # Simple density
        )
        
        # 4. Audit
        if detected_pii_list:
             self.log_event("PII_DETECTED", {
                 "chunk_id": chunk.chunk_id,
                 "count": len(detected_pii_list),
                 "types": list(set(d.entity_type for d in detected_pii_list))
             })
             
        return classified

    def _add_aadhaar_recognizer(self):
        """Adds custom regex for Indian Aadhaar."""
        # 12 digits, optional spaces/dashes (Naive for Demo)
        aadhaar_pattern = Pattern(name="aadhaar_pattern", regex=r"\b\d{4}\s?\d{4}\s?\d{4}\b", score=0.85)
        recognizer = PatternRecognizer(supported_entity="IN_AADHAAR", patterns=[aadhaar_pattern])
        self.analyzer.registry.add_recognizer(recognizer)

    def _add_pan_recognizer(self):
        """Adds custom regex for Indian PAN Card."""
        # 5 letters, 4 digits, 1 letter
        pan_pattern = Pattern(name="pan_pattern", regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", score=0.85)
        recognizer = PatternRecognizer(supported_entity="IN_PAN", patterns=[pan_pattern])
        self.analyzer.registry.add_recognizer(recognizer)
