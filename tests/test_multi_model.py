
import sys
import os
import json
import pandas as pd

sys.path.append(os.path.abspath("."))

from agents.extractor import ExtractorAgent

def test_multi_model():
    print("Testing Multi-Model Ingestion...\n")
    agent = ExtractorAgent()
    
    # 1. Test Excel (Real User File)
    xlsx_path = r"c:\Users\Kandukoori Tejaswini\NDRA-PII\NDRA\datasets\Testing_Set.xlsx"
    if os.path.exists(xlsx_path):
        print(f"--- Processing Excel: {xlsx_path} ---")
        try:
            chunks = agent.process(xlsx_path)
            print(f"[OK] Extracted {len(chunks)} chunks from Excel.")
            if chunks:
                print(f"Preview: {chunks[0].processed_text[:100]}...")
        except Exception as e:
            print(f"[FAIL] Excel Processing: {e}")
    else:
        print("[SKIP] Testing_Set.xlsx not found.")

    # 2. Test JSON (Synthetic)
    json_path = "test_data.json"
    data = {"name": "John Doe", "email": "john@example.com", "role": "admin"}
    with open(json_path, "w") as f:
        json.dump(data, f)
        
    print(f"\n--- Processing JSON: {json_path} ---")
    chunks = agent.process(json_path)
    print(f"[OK] Extracted {len(chunks)} chunks from JSON.")
    print(f"Preview: {chunks[0].processed_text}")
    
    # Cleanup
    if os.path.exists(json_path):
        os.remove(json_path)

if __name__ == "__main__":
    test_multi_model()
