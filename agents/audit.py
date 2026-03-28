
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
    The hash chain is persisted to disk so that it survives process restarts.
    """
    def __init__(self, log_file: str = None):
        super().__init__("AuditAgent")
        self.log_file = log_file or os.getenv("AUDIT_LOG_FILE", "audit.log")
        log_parent = os.path.dirname(self.log_file)
        if log_parent:
            os.makedirs(log_parent, exist_ok=True)
        # Restore the last known hash from the existing log so the chain remains
        # unbroken across process restarts.
        self.last_hash = self._read_last_hash()

    def _read_last_hash(self) -> str:
        """Read the last hash from the audit log to resume the chain after restart.

        Reads from the end of the file so performance is O(1) regardless of
        log size rather than O(n).
        """
        genesis = "0" * 64
        if not os.path.exists(self.log_file):
            return genesis
        try:
            with open(self.log_file, "rb") as f:
                # Seek backwards to find the last non-empty line
                f.seek(0, 2)  # end of file
                file_size = f.tell()
                if file_size == 0:
                    return genesis

                # Read up to 4 KiB from the end — more than enough for one JSONL entry
                read_size = min(4096, file_size)
                f.seek(-read_size, 2)
                tail = f.read(read_size).decode("utf-8", errors="replace")

            last_line = ""
            for line in reversed(tail.splitlines()):
                line = line.strip()
                if line:
                    last_line = line
                    break

            if last_line:
                entry = json.loads(last_line)
                return entry.get("hash", genesis)
        except Exception as e:
            self.logger.warning(f"Could not restore audit chain from log: {e}")
        return genesis

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
