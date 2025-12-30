
from abc import ABC, abstractmethod
from typing import Any, Dict
import logging
import uuid
from datetime import datetime

# Setup structured logging (Phase 1 Requirement)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
            "details": details
        }
        self.logger.info(f"AUDIT_EVENT: {log_entry}")

    def health_check(self) -> bool:
        """
        Basic health check.
        """
        return True
