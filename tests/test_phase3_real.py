
import sys
import os

sys.path.append(os.path.abspath("."))

from agents.extractor import ExtractorAgent
from agents.classifier import ClassifierAgent

def test_phase_3_real():
    print("Testing Phase 3 (PII Detection) on Real Doc...")
    
    # 1. Ingest
    pdf_path = r"c:\Users\Kandukoori Tejaswini\NDRA-PII\NDRA\datasets\Testing_Set.pdf"
    extractor = ExtractorAgent()
    classifier = ClassifierAgent()
    
    print("Step 1: Extracting...")
    semantic_chunks = extractor.process(pdf_path)
    print(f"[OK] Extracted {len(semantic_chunks)} chunks.")
    
    # 2. Detect
    print("Step 2: Detecting PII (Presidio + Custom)...")
    pii_count = 0
    
    for i, chunk in enumerate(semantic_chunks):
        # Only process first 5 for demo speed, or all if small
        classified_chunk = classifier.process(chunk)
        
        if classified_chunk.detected_entities:
            pii_count += len(classified_chunk.detected_entities)
            print(f"\n--- Chunk {i+1} PII Detected ---")
            for pii in classified_chunk.detected_entities:
                loc_str = "N/A"
                if pii.location:
                   loc_str = f"Page {pii.location.page_number} [{pii.location.char_start_on_page}:{pii.location.char_end_on_page}]" 
                
                print(f"[{pii.entity_type}] Score: {pii.score:.2f} | Text: '{pii.text_value}' | Loc: {loc_str}")
    
    print(f"\n[OK] Total PII Entities Detected: {pii_count}")

if __name__ == "__main__":
    test_phase_3_real()
