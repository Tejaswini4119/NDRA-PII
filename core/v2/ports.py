from typing import List, Protocol
from schemas.core_models import ClassifiedChunk, GovernedChunk, SemanticChunk


class ExtractorPort(Protocol):
    def process(self, file_path: str, context: dict | None = None) -> List[SemanticChunk]:
        ...


class ClassifierPort(Protocol):
    def process(self, chunk: SemanticChunk, context: dict | None = None) -> ClassifiedChunk:
        ...


class FusionPort(Protocol):
    def fuse_chunk(self, chunk: ClassifiedChunk) -> ClassifiedChunk:
        ...

    def fuse_cross_chunks(self, chunks: List[ClassifiedChunk]) -> List[ClassifiedChunk]:
        ...


class PolicyPort(Protocol):
    def evaluate_chunk(self, chunk: ClassifiedChunk, trace_id: str = "unknown") -> GovernedChunk:
        ...


class RedactionPort(Protocol):
    def redact(self, chunk: GovernedChunk) -> GovernedChunk:
        ...
