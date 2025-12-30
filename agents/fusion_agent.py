from typing import List
from schemas.core_models import DetectedPII, ClassifiedChunk

class FusionAgent:
    """
    Agent responsible for deduplicating and resolving PII entities.
    Phase 4: PII Fusion.
    """

    def __init__(self):
        pass

    def deduplicate_entities(self, entities: List[DetectedPII]) -> List[DetectedPII]:
        """
        Deduplicates overlapping entities within a single list (chunk).
        Strategy:
        1. Exact duplicates: Keep one.
        2. Included intervals: If A contains B, keep A.
        3. Partial overlaps: Keep the longer one (or higher score if same length).
        """
        if not entities:
            return []

        # Sort by start_index, then by end_index (descending) to prioritize longer matches starting at same pos
        sorted_entities = sorted(entities, key=lambda x: (x.start_index, -x.end_index))
        
        merged = []
        
        for current in sorted_entities:
            if not merged:
                merged.append(current)
                continue
            
            last = merged[-1]
            
            # Check for overlap
            if current.start_index < last.end_index:
                # Overlap detected
                
                # Case 1: containment. Last contains Current.
                # Since we sorted by start_index, Last.start <= Current.start.
                # We just need to check if Last.end >= Current.end.
                if last.end_index >= current.end_index:
                    # Current is inside Last.
                    
                    # Check for exact span match (same length)
                    if (last.end_index - last.start_index) == (current.end_index - current.start_index):
                         if current.score > last.score:
                             merged.pop()
                             merged.append(current)
                    
                    # If Last is longer, we keep Last (ignore Current)
                    continue
                
                # Case 2: Partial overlap.
                # Last: [---]
                # Curr:   [---]
                # We need to decide which to keep.
                
                # Length check
                last_len = last.end_index - last.start_index
                curr_len = current.end_index - current.start_index
                
                if curr_len > last_len:
                    # Current is longer, replace Last
                    merged.pop()
                    merged.append(current)
                elif curr_len < last_len:
                    # Last is longer, keep Last (ignore Current)
                    continue
                else:
                    # Same length. Check score.
                    if current.score > last.score:
                         merged.pop()
                         merged.append(current)
            else:
                # No overlap
                merged.append(current)
                
        return merged

    def fuse_chunk(self, chunk: ClassifiedChunk) -> ClassifiedChunk:
        """
        Applies fusion logic to a ClassifiedChunk.
        """
        original_count = len(chunk.detected_entities)
        fused_entities = self.deduplicate_entities(chunk.detected_entities)
        chunk.detected_entities = fused_entities
        # Recalculate density if needed, though usually semantic density is about token coverage.
        # But simple count might have changed.
        return chunk
