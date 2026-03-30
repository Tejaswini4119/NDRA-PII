import sys
import os
from pathlib import Path
import unittest

# Add root to path
sys.path.append(os.path.abspath("."))

from agents.extractor import ExtractorAgent

def test_real_doc():
    pdf_path = Path(__file__).resolve().parents[1] / "datasets" / "Testing_Set.pdf"
    
    if not pdf_path.exists():
        raise unittest.SkipTest("datasets/Testing_Set.pdf not found in workspace")

    print(f"Testing real document: {pdf_path}")
    
    agent = ExtractorAgent()
    try:
        chunks = agent.process(str(pdf_path))
        
        print(f"\n[OK] Extracted {len(chunks)} chunks.")
        
        # Print first few chunks to verify content
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- Chunk {i+1} (Page {chunk.page_number}) ---")
            print(f"ID: {chunk.chunk_id}")
            print(f"Text Preview: {chunk.processed_text[:200]}...")
            print("-" * 50)
            
    except Exception as e:
        print(f"[FAIL] Extraction failed: {e}")

if __name__ == "__main__":
    test_real_doc()
