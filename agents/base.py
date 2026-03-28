
from abc import ABC, abstractmethod
from typing import Any, Dict
import json
import logging
import uuid
from datetime import datetime


class _JsonFormatter(logging.Formatter):
    """
    Emits each log record as a single-line JSON object, suitable for
    ingestion by ELK, Splunk, or any cloud SIEM platform.
    """

    def format(self, record: logging.LogRecord) -> str:
        obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            obj["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            obj["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(obj)


def _configure_logging() -> None:
    """Configure the root logger with the JSON formatter.

    Called once at module import time.  If any handlers are already attached
    to the root logger (e.g. by pytest, uvicorn, or a third-party library
    loaded before this module), this function skips configuration entirely to
    avoid overriding the caller's setup.  As a consequence, log records
    emitted before this module is imported may use a different format.  In
    production, ensure this module is imported early in the application
    startup sequence to guarantee consistent JSON formatting.
    """
    root = logging.getLogger()
    if root.handlers:
        # Handlers already present — respect the existing configuration.
        return
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    root.setLevel(logging.INFO)
    root.addHandler(handler)


_configure_logging()


class NDRAAgent(ABC):
    """
    Abstract Base Agent for NDRA-PII.
    Enforces distinct responsibility, tracing, and standardized interfaces.
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"NDRA.{agent_name}")
        self.agent_id = str(uuid.uuid4())
        self.logger.info(f"Agent Initialized: {self.agent_name} (ID: {self.agent_id})")

    @abstractmethod
    def process(self, input_data: Any, context: Dict[str, Any] = None) -> Any:
        """
        Main execution method. MUST be idempotent.
        """
        pass

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """
        Emits a structured log event for auditability.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.agent_name,
            "event": event_type,
            "details": details,
        }
        self.logger.info(f"AUDIT_EVENT: {log_entry}")

    def health_check(self) -> bool:
        """
        Basic health check.
        """
        return True
