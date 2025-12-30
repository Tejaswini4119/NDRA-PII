
import sys
import os

# Add root to path
sys.path.append(os.path.abspath("."))

from agents.audit import AuditAgent
from schemas.core_models import DocumentMetadata
from config.settings import settings

def test_phase_1():
    print(f"Testing {settings.APP_NAME}...")
    
    # 1. Test Config
    assert settings.ENV in ["dev", "prod"]
    print("[OK] Config Loaded")
    
    # 2. Test Schemas
    doc = DocumentMetadata(
        filename="test.pdf", 
        file_size_bytes=1024, 
        mime_type="application/pdf", 
        sha256_hash="abc"
    )
    print(f"[OK] Schema Valid: {doc.filename}")
    
    # 3. Test Audit Agent
    agent = AuditAgent(log_file="test_audit.log")
    entry = agent.process({"action": "test_boot"}, context={})
    print(f"[OK] Audit Logged: {entry['hash']}")
    
    # Clean up
    if os.path.exists("test_audit.log"):
        os.remove("test_audit.log")

if __name__ == "__main__":
    test_phase_1()
