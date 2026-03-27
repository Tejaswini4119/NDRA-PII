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

    def fuse_cross_chunks(self, chunks: List[ClassifiedChunk]) -> List[ClassifiedChunk]:
        """
        Resolves entities split cleanly across chunk boundaries.
        Processes chunks sequentially and links trailing entities of chunk_a 
        with leading entities of chunk_b.
        """
        if not chunks or len(chunks) < 2:
            return chunks

        for i in range(len(chunks) - 1):
            chunk_a = chunks[i]
            chunk_b = chunks[i+1]
            
            if not chunk_a.detected_entities or not chunk_b.detected_entities:
                continue
                
            # Sort entities by position
            a_entities = sorted(chunk_a.detected_entities, key=lambda e: e.start_index)
            b_entities = sorted(chunk_b.detected_entities, key=lambda e: e.start_index)
            
            # Trailing entity in Chunk A
            trailing_a = a_entities[-1]
            # Leading entity in Chunk B
            leading_b = b_entities[0]
            
            # Check proximity to boundaries
            chunk_a_len = len(chunk_a.processed_text)
            
            # Define proximity threshold (e.g. 10 chars from boundary to account for whitespace/punctuation)
            a_proximity = chunk_a_len - trailing_a.end_index
            b_proximity = leading_b.start_index
            
            if a_proximity <= 10 and b_proximity <= 10:
                if trailing_a.entity_type == leading_b.entity_type:
                    # Link them (Option B)
                    combined_text = trailing_a.text_value + " " + leading_b.text_value
                    
                    # Update text_value so Policy considers the combined string
                    trailing_a.text_value = combined_text.strip()
                    leading_b.text_value = combined_text.strip()
                    
                    # Boost score slightly to reflect combined confidence
                    max_score = max(trailing_a.score, leading_b.score)
                    trailing_a.score = min(max_score + 0.1, 1.0)
                    leading_b.score = min(max_score + 0.1, 1.0)

        return chunks
