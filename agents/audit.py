
import json
import hashlib
import os
import threading
from datetime import datetime
from typing import Any, Dict
from agents.base import NDRAAgent

class AuditAgent(NDRAAgent):
    """
    Responsible for immutable, tamper-evident logging of all system decisions.
    Phase 1: Basic JSONL logging with SHA-256 chaining.
    The hash chain is persisted to disk so that it survives process restarts.
    Thread-safe: a lock protects the in-memory last_hash and the append write
    so that concurrent requests cannot corrupt the chain.
    """
    def __init__(self, log_file: str = None):
        super().__init__("AuditAgent")
        self.log_file = log_file or os.getenv("AUDIT_LOG_FILE", "audit.log")
        log_parent = os.path.dirname(self.log_file)
        if log_parent:
            os.makedirs(log_parent, exist_ok=True)
        self._lock = threading.Lock()
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
        Thread-safe: the lock ensures the hash chain is updated atomically.
        """
        timestamp = datetime.utcnow().isoformat()

        with self._lock:
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

            # Append to log file (Immutable append-only) — inside the lock so
            # the hash and the write are an atomic unit.
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

        self.logger.info(f"Audit Logged: {curr_hash[:8]}...")
        return entry

    def verify_chain(self) -> Dict[str, Any]:
        """Walk the entire audit log and verify the SHA-256 hash chain.

        Each entry's ``prev_hash`` must equal the hash stored in the
        preceding entry.  The hash of each entry's ``payload`` is also
        recomputed and compared against the stored ``hash`` field to detect
        tampering.

        Returns:
            A dict with the following keys:

            * ``valid`` (bool) — True if the entire chain is intact.
            * ``entries_verified`` (int) — Number of entries successfully
              verified before any failure (or the total if fully valid).
            * ``first_broken_at`` (int | None) — 1-based line number of the
              first broken entry, or None if the chain is intact.
            * ``error`` (str | None) — Human-readable description of the
              failure, or None if valid.
        """
        if not os.path.exists(self.log_file):
            return {
                "valid": True,
                "entries_verified": 0,
                "first_broken_at": None,
                "error": None,
            }

        try:
            prev_hash = "0" * 64
            entries_verified = 0

            with open(self.log_file, "r", encoding="utf-8") as f:
                for line_num, raw_line in enumerate(f, start=1):
                    line = raw_line.strip()
                    if not line:
                        continue

                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError as exc:
                        return {
                            "valid": False,
                            "entries_verified": entries_verified,
                            "first_broken_at": line_num,
                            "error": f"JSON parse error at line {line_num}: {exc}",
                        }

                    payload = entry.get("payload", {})

                    # 1. Verify prev_hash link
                    stored_prev = payload.get("prev_hash", "")
                    if stored_prev != prev_hash:
                        return {
                            "valid": False,
                            "entries_verified": entries_verified,
                            "first_broken_at": line_num,
                            "error": (
                                f"Chain broken at entry {line_num}: "
                                f"expected prev_hash={prev_hash[:16]}…, "
                                f"got {stored_prev[:16]}…"
                            ),
                        }

                    # 2. Recompute the entry hash and compare
                    payload_str = json.dumps(payload, sort_keys=True)
                    expected_hash = hashlib.sha256(
                        payload_str.encode("utf-8")
                    ).hexdigest()
                    stored_hash = entry.get("hash", "")
                    if stored_hash != expected_hash:
                        return {
                            "valid": False,
                            "entries_verified": entries_verified,
                            "first_broken_at": line_num,
                            "error": (
                                f"Hash mismatch at entry {line_num}: "
                                f"stored={stored_hash[:16]}…, "
                                f"recomputed={expected_hash[:16]}…"
                            ),
                        }

                    prev_hash = stored_hash
                    entries_verified += 1

            return {
                "valid": True,
                "entries_verified": entries_verified,
                "first_broken_at": None,
                "error": None,
            }

        except Exception as exc:
            return {
                "valid": False,
                "entries_verified": 0,
                "first_broken_at": None,
                "error": str(exc),
            }
