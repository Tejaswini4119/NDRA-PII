
import json
import hashlib
import os
from datetime import datetime
from typing import Any, Dict
from agents.base import NDRAAgent

class AuditAgent(NDRAAgent):
    """
    Responsible for immutable, tamper-evident logging of all system decisions.
    Phase 1: Basic JSONL logging with SHA-256 chaining.
    """
    def __init__(self, log_file: str = None):
        super().__init__("AuditAgent")
        self.log_file = log_file or os.getenv("AUDIT_LOG_FILE", "audit.log")
        log_parent = os.path.dirname(self.log_file)
        if log_parent:
            os.makedirs(log_parent, exist_ok=True)
        self.last_hash = "0" * 64  # Genesis hash

    def process(self, input_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Record a decision/event.
        Input: Dict containing 'event_type', 'data', 'agent_source'.
        Output: The recorded log entry with hash.
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Create canonical string for hashing
        payload = {
            "timestamp": timestamp,
            "prev_hash": self.last_hash,
            "event": input_data
        }
        
        # Serialize deterministically
        payload_str = json.dumps(payload, sort_keys=True)
        
        # Compute Hash (SHA-256)
        curr_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        self.last_hash = curr_hash
        
        entry = {
            "hash": curr_hash,
            "payload": payload
        }
        
        # Append to log file (Immutable append-only)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
            
        self.logger.info(f"Audit Logged: {curr_hash[:8]}...")
        return entry
