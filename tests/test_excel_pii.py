
import sys
import os
from pathlib import Path
import unittest

sys.path.append(os.path.abspath("."))

from agents.extractor import ExtractorAgent
from agents.classifier import ClassifierAgent

def test_excel_detailed():
    print("Testing Detailed PII Detection on Excel...\n")
    
    xlsx_path = Path(__file__).resolve().parents[1] / "datasets" / "Testing_Set.xlsx"
    if not xlsx_path.exists():
        raise unittest.SkipTest("datasets/Testing_Set.xlsx not found in workspace")

    # 1. Ingest
    extractor = ExtractorAgent()
    chunks = extractor.process(str(xlsx_path))
    print(f"[OK] Ingested Excel: {len(chunks)} chunks.")

    # 2. Detect
    classifier = ClassifierAgent()
    total_pii = 0
    
    print("\n--- Detailed Findings ---")
    for i, chunk in enumerate(chunks):
        classified = classifier.process(chunk)
        if classified.detected_entities:
            total_pii += len(classified.detected_entities)
            print(f"\n[Chunk {i+1}] (Sheet/Page {chunk.page_number})")
            for pii in classified.detected_entities:
                loc_str = "N/A"
                if pii.location:
                    # For Excel, Page 1 usually means Sheet 1 (unless multiple sheets processed)
                    loc = pii.location
                    loc_str = f"Offset [{loc.char_start_on_page}:{loc.char_end_on_page}]"
                
                print(f"  -> [{pii.entity_type}] '{pii.text_value}' | Score: {pii.score:.2f} | {loc_str}")
                # Optional: Show context
                if pii.location and pii.location.nearby_context:
                    safe_context = pii.location.nearby_context.encode('ascii', 'ignore').decode('ascii').replace('\n', ' ')
                    print(f"     Context: ...{safe_context}...")

    print(f"\n[OK] Total PII Detected in Excel: {total_pii}")

if __name__ == "__main__":
    test_excel_detailed()
