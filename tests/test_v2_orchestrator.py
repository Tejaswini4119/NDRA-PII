import unittest

from core.v2.models import PipelineContext
from core.v2.pipeline import V2PipelineOrchestrator
from core.v2.settings import V2RuntimeSettings
from schemas.core_models import (
    AgentDecision,
    ClassifiedChunk,
    DetectedPII,
    GovernedChunk,
    SemanticChunk,
)


class FakeExtractor:
    def process(self, file_path, context=None):
        return [
            SemanticChunk(
                document_id="doc-1",
                processed_text="Contact me at john@example.com",
                original_text="Contact me at john@example.com",
                page_number=1,
                token_span=(0, 30),
            )
        ]


class FakeClassifier:
    def process(self, chunk, context=None):
        return ClassifiedChunk(
            **chunk.model_dump(),
            detected_entities=[
                DetectedPII(
                    entity_type="EMAIL_ADDRESS",
                    text_value="john@example.com",
                    start_index=14,
                    end_index=30,
                    score=0.95,
                    source="test",
                )
            ],
            pii_density_score=0.2,
        )


class FakeFusion:
    def fuse_chunk(self, chunk):
        return chunk

    def fuse_cross_chunks(self, chunks):
        return chunks


class FakePolicy:
    def evaluate_chunk(self, chunk, trace_id="unknown"):
        decision = AgentDecision(
            trace_id=trace_id,
            chunk_id=chunk.chunk_id,
            agent_name="PolicyAgent",
            action="Redact",
            risk_score=0.8,
            justification_trace=["test policy fired"],
        )
        return GovernedChunk(**chunk.model_dump(), redacted_text=chunk.processed_text, decision=decision)


class FakeRedaction:
    def redact(self, chunk):
        chunk.redacted_text = chunk.processed_text.replace("john@example.com", "[EMAIL_ADDRESS]")
        return chunk


class TestV2Orchestrator(unittest.TestCase):
    def test_pipeline_success(self):
        orchestrator = V2PipelineOrchestrator(
            extractor=FakeExtractor(),
            classifier=FakeClassifier(),
            fusion=FakeFusion(),
            policy=FakePolicy(),
            redaction=FakeRedaction(),
            settings=V2RuntimeSettings(max_processing_seconds=60),
        )

        result = orchestrator.run(
            file_path="/tmp/dummy.txt",
            context=PipelineContext(trace_id="trace-1", filename="dummy.txt"),
        )

        self.assertEqual(result.status, "processed")
        self.assertEqual(result.pii_detected_count, 1)
        self.assertEqual(result.final_action, "Redact")
        self.assertTrue(len(result.step_metrics) >= 3)

    def test_pipeline_fails_on_chunk_limit(self):
        class ManyChunkExtractor:
            def process(self, file_path, context=None):
                return [
                    SemanticChunk(
                        document_id="doc-1",
                        processed_text="hello",
                        original_text="hello",
                        page_number=1,
                        token_span=(0, 5),
                    ),
                    SemanticChunk(
                        document_id="doc-1",
                        processed_text="world",
                        original_text="world",
                        page_number=1,
                        token_span=(6, 11),
                    ),
                ]

        orchestrator = V2PipelineOrchestrator(
            extractor=ManyChunkExtractor(),
            classifier=FakeClassifier(),
            fusion=FakeFusion(),
            policy=FakePolicy(),
            redaction=FakeRedaction(),
            settings=V2RuntimeSettings(max_chunks_per_document=1, fail_closed=True),
        )

        result = orchestrator.run(
            file_path="/tmp/dummy.txt",
            context=PipelineContext(trace_id="trace-2", filename="dummy.txt"),
        )

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.final_action, "Quarantine")
        self.assertIn("Chunk limit exceeded", result.diagnostics.get("error", ""))


if __name__ == "__main__":
    unittest.main()
