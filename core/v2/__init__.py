"""NDRA v2 core architecture package.

This package contains production-oriented orchestration contracts and
composable pipeline utilities used by the next-generation NDRA runtime.
"""

from .pipeline import V2PipelineOrchestrator
from .settings import V2RuntimeSettings

__all__ = ["V2PipelineOrchestrator", "V2RuntimeSettings"]
