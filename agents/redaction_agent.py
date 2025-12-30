from schemas.core_models import GovernedChunk
import logging

logger = logging.getLogger(__name__)

class RedactionAgent:
    """
    Agent responsible for applying redaction masks to text based on Policy decisions.
    Phase 6: Redaction.
    """
    
    def __init__(self):
        pass

    def redact(self, chunk: GovernedChunk) -> GovernedChunk:
        """
        Applies redaction if the decision is 'Redact'.
        Uses PII offsets to replace text with [<ENTITY_TYPE>].
        """
        # 1. Check if redaction is required
        if chunk.decision.action != "Redact":
            chunk.redacted_text = chunk.processed_text
            return chunk

        if not chunk.detected_entities:
            chunk.redacted_text = chunk.processed_text
            return chunk

        original_text = chunk.processed_text
        redacted_chars = list(original_text)
        
        # 2. Sort entities by start_index descending to handle replacements correctly
        # Actually, if we use character list replacement, order matters less if we don't insert/delete, 
        # but we are replacing variable length text with variable length placeholders.
        # So we MUST go from end to start to avoid shifting index problems.
        
        sorted_entities = sorted(chunk.detected_entities, key=lambda x: x.start_index, reverse=True)
        
        for entity in sorted_entities:
            start = entity.start_index
            end = entity.end_index
            
            # Sanity check bounds
            if start < 0 or end > len(original_text):
                logger.warning(f"Skipping OOB entity: {entity.text_value} [{start}:{end}] in text len {len(original_text)}")
                continue
                
            # Create replacement string
            replacement = f"[{entity.entity_type}]"
            
            # Apply replacement to the list of characters
            # But wait, replacing a slice in a list with a string (iterable) works, 
            # but it changes the indices of everything after it.
            # That is why we iterate REVERSE (end to start).
            
            # redacted_chars[start:end] = list(replacement) 
            # This is the correct pythonic way to replace a slice.
            
            # Note: We need to be careful about overlapping entities.
            # Phase 4 (Fusion) should have removed overlaps. 
            # If implementation failed, overlaps might cause weirdness here.
            # Assuming Fusion did its job.
            
            redacted_chars[start:end] = list(replacement)

        chunk.redacted_text = "".join(redacted_chars)
        return chunk
