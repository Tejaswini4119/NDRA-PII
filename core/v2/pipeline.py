from __future__ import annotations

from time import monotonic
from typing import List

from schemas.core_models import ClassifiedChunk

from .models import OrchestrationStepMetric, PipelineContext, PipelineOutput
from .ports import ClassifierPort, ExtractorPort, FusionPort, PolicyPort, RedactionPort
from .settings import V2RuntimeSettings


class V2PipelineOrchestrator:
    """Production-oriented orchestration shell for NDRA v2.

    This class centralizes runtime safeguards and deterministic execution while
    delegating extraction/classification/policy/redaction work to pluggable ports.
    """

    def __init__(
        self,
        extractor: ExtractorPort,
        classifier: ClassifierPort,
        fusion: FusionPort,
        policy: PolicyPort,
        redaction: RedactionPort,
        settings: V2RuntimeSettings | None = None,
    ):
        self.extractor = extractor
        self.classifier = classifier
        self.fusion = fusion
        self.policy = policy
        self.redaction = redaction
        self.settings = settings or V2RuntimeSettings()

    def run(self, file_path: str, context: PipelineContext) -> PipelineOutput:
        pipeline_start = monotonic()
        metrics: List[OrchestrationStepMetric] = []

        chunks = self._timed_extract(file_path, metrics)
        if len(chunks) > self.settings.max_chunks_per_document:
            return self._failed_result(
                context=context,
                metrics=metrics,
                diagnostics={"error": "Chunk limit exceeded"},
            )

        classified_chunks = self._timed_classify(chunks, metrics)
        fused_chunks = self._timed_fuse(classified_chunks, metrics)

        total_pii = 0
        policy_decisions = 0
        final_action = "Allow"
        redacted_preview = None

        for chunk in fused_chunks:
            governed = self.policy.evaluate_chunk(chunk, trace_id=context.trace_id)
            redacted = self.redaction.redact(governed)

            if redacted.decision.action != "Allow" or redacted.decision.risk_score > 0:
                policy_decisions += 1

            if redacted.detected_entities:
                total_pii += len(redacted.detected_entities)
                if redacted_preview is None:
                    redacted_preview = redacted.redacted_text[:300]

            if redacted.decision.action in {"Block", "Quarantine", "Escalate", "Redact"}:
                final_action = redacted.decision.action

            if len(redacted.detected_entities) > self.settings.max_entities_per_chunk:
                return self._failed_result(
                    context=context,
                    metrics=metrics,
                    diagnostics={"error": "Entity limit exceeded"},
                )

            if monotonic() - pipeline_start > self.settings.max_processing_seconds:
                return self._failed_result(
                    context=context,
                    metrics=metrics,
                    diagnostics={"error": "Processing timeout exceeded"},
                )

        return PipelineOutput(
            trace_id=context.trace_id,
            filename=context.filename,
            status="processed",
            chunks_count=len(chunks),
            pii_detected_count=total_pii,
            policy_decisions_count=policy_decisions,
            final_action=final_action,
            redacted_text_preview=redacted_preview,
            step_metrics=metrics,
            diagnostics={},
        )

    def _timed_extract(self, file_path: str, metrics: List[OrchestrationStepMetric]):
        start = monotonic()
        chunks = self.extractor.process(file_path)
        metrics.append(
            OrchestrationStepMetric(
                name="extract",
                elapsed_ms=int((monotonic() - start) * 1000),
            )
        )
        return chunks

    def _timed_classify(self, chunks, metrics: List[OrchestrationStepMetric]) -> List[ClassifiedChunk]:
        start = monotonic()
        classified = []
        for chunk in chunks:
            classified.append(self.classifier.process(chunk))
        metrics.append(
            OrchestrationStepMetric(
                name="classify",
                elapsed_ms=int((monotonic() - start) * 1000),
            )
        )
        return classified

    def _timed_fuse(self, classified_chunks: List[ClassifiedChunk], metrics: List[OrchestrationStepMetric]):
        start = monotonic()
        intra = [self.fusion.fuse_chunk(chunk) for chunk in classified_chunks]
        fused = self.fusion.fuse_cross_chunks(intra)
        metrics.append(
            OrchestrationStepMetric(
                name="fuse",
                elapsed_ms=int((monotonic() - start) * 1000),
            )
        )
        return fused

    def _failed_result(
        self,
        context: PipelineContext,
        metrics: List[OrchestrationStepMetric],
        diagnostics: dict,
    ) -> PipelineOutput:
        return PipelineOutput(
            trace_id=context.trace_id,
            filename=context.filename,
            status="failed",
            chunks_count=0,
            pii_detected_count=0,
            policy_decisions_count=0,
            final_action="Quarantine" if self.settings.fail_closed else "Allow",
            redacted_text_preview=None,
            step_metrics=metrics,
            diagnostics=diagnostics,
        )
