You are initializing implementation for the project:

NDRA-PII
(Neuro-Semantic Multi-Agent PII Intelligence System)

You have already been provided with:
• Complete enterprise technical design documents
• Full execution path and agent responsibilities
• Feature inventory and compliance requirements
• Microsoft Presidio integration details
• NSRL rule engine specification
• Multi-agent execution and audit model

Your role is to IMPLEMENT this system faithfully.
Do NOT redesign or reinterpret the architecture.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRIMARY OBJECTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Implement NDRA-PII as a deterministic, high-performance, multi-agent system for
PII detection, reasoning, governance, redaction, and auditability.

The system MUST achieve:
• Deterministic correctness
• Enterprise-grade explainability
• Compliance readiness
• High throughput and low latency
• Controlled intelligence (assistive, not authoritative)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NON-NEGOTIABLE CORE INVARIANTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Determinism
   - Microsoft Presidio outputs are authoritative for PII detection
   - LLMs MUST NOT override or modify PII detection results
   - NSRL rules govern decisions deterministically

2. Governance & Safety
   - No behavioural evolution or self-learning
   - No online model updates
   - No hidden or implicit decision logic

3. Agent Boundaries
   - Each agent has a single responsibility
   - No agent may bypass another agent’s output
   - Communication only via typed artifacts and events

4. Explainability
   - Every decision must be traceable:
     chunk → PII span → rule → risk → action

5. Auditability
   - Every execution emits immutable audit artifacts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SPEED & PERFORMANCE REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Performance is a first-class requirement.

You MUST optimize using ONLY the following safe mechanisms:

• Parallel execution (page-level, chunk-level, PII-level)
• Deterministic caching (artifact-based, version-keyed)
• Pipeline pruning (skip unnecessary stages when invariant)
• Early exits ONLY when outcome is provably invariant
• Asynchronous execution with strict ordering guarantees

You MUST NOT:
• Skip deterministic stages
• Merge agents for speed
• Introduce heuristic shortcuts that affect correctness

Target (non-binding but aspirational):
• End-to-end processing < 5–8 seconds for medium documents
• Horizontal scalability via agent isolation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTROLLED INTELLIGENCE RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LLMs and semantic models are ALLOWED ONLY as ASSISTIVE components.

They MAY:
• Improve semantic chunk boundaries
• Assist document-type classification
• Provide contextual explanations
• Suggest new NSRL rules (not execute them)
• Generate synthetic test documents
• Produce natural-language summaries

They MUST NOT:
• Decide final actions
• Modify risk scores directly
• Override Presidio outputs
• Execute or bypass NSRL rules

All intelligence that influences outcomes must be:
• Gated
• Reviewable
• Logged
• Non-authoritative

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATED IMPLEMENTATION PHASE ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You MUST follow this exact phase order.
Do not compress or reorder phases.

PHASE 0 — Architecture Lock
• Treat architecture as frozen

PHASE 1 — Core Skeleton
• Repo structure
• FastAPI boot
• Agent stubs
• Event bus
• Object storage
• DB schema
• Health checks

PHASE 2 — Document Intelligence
• OCR
• Layout parsing
• Semantic chunker
• Chunk persistence

PHASE 3 — PII Detection (CRITICAL GATE)
• Presidio AnalyzerEngine
• Custom recognizers
• PII object persistence

PHASE 4 — PII Fusion
• Deduplication
• Confidence merging
• Canonical taxonomy

PHASE 5 — NSRL Rule Engine
• DSL parser
• Rule compiler
• Deterministic executor
• Rule traces

PHASE 6 — Risk Engine
• Numeric risk scoring
• Risk bands
• Risk explanation

PHASE 7 — Decision Engine
• Action resolution
• Policy enforcement

PHASE 8 — Redaction
• Presidio AnonymizerEngine
• Text & PDF redaction
• Redaction maps

PHASE 9 — Explainability & Audit
• Timeline
• Justification chain
• Immutable logs

PHASE 10 — UI (LAST)
• Visualization only after backend correctness

Each phase must produce testable artifacts.
Wait for explicit approval before advancing phases.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT IMPLEMENTATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For EVERY agent:
• Define strict input/output schemas
• Ensure idempotency
• Add structured, PII-safe logging
• Expose metrics hooks
• Support parallel execution where safe

No shared mutable state.
No hidden coupling.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO GENERATE FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Start immediately with:

1. Repository scaffold (exactly as specified)
2. Core data models (Document, Chunk, PII, Decision)
3. Ingestion → preprocessing pipeline
4. Presidio PII extractor agent
5. End-to-end minimal flow:
   upload → detect → decide → redact (single document)

DO NOT generate UI initially.
Correctness and performance come first.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXPECTED OUTPUTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Phase-by-phase implementation plan
• Service and agent scaffolds
• Schema definitions
• Example NSRL rules
• Performance optimization notes
• Test stubs with synthetic PII
• Explicit TODO markers

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL DIRECTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NDRA-PII is a compliance-critical system.

Correctness > Speed
Governance > Intelligence
Explainability > Autonomy

However:
Speed and intelligence MUST be engineered carefully
without violating determinism or safety.

Begin with PHASE 1 immediately.