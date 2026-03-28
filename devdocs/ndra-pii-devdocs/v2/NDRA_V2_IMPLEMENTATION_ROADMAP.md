# NDRA-PII v2 Implementation Roadmap (Production Program)

## 1) Reality Check

"100% production readiness" is not a one-time coding event. It is an engineering program with strict gates:

- Architecture and threat model sign-off
- Security hardening and compliance evidence
- Reliability SLO/SLA proof
- Continuous verification in CI/CD and runtime

This roadmap starts v2 immediately with those gates built in.

## 2) Critical v1 Architectural Flaws (Observed)

1. Single-process, tightly coupled runtime in main.py with shared mutable objects.
2. No job queue or backpressure strategy for large or concurrent workloads.
3. Request lifecycle and document pipeline lifecycle are tightly bound (limited retry isolation).
4. Policy loading is startup-only and lacks version pinning, signature verification, and atomic rollout.
5. Archive extraction in extractor is unsafe for production (zip/tar path traversal and decompression bomb risk).
6. Logging and audit are unstructured for compliance-grade evidence and correlation across services.
7. No deterministic idempotency model for repeat submissions.
8. Security posture missing: rate limits, content-type trust boundaries, strict upload validation, malware scan integration.
9. Test strategy has weak environment-independent coverage and has hard-coded local paths in multiple tests.
10. No migration-safe contract layer between domain logic and adapters.

## 3) v2 Target Architecture

## 3.1 Architectural Style

- Hexagonal architecture (ports/adapters)
- Event-aware orchestration (sync first, async-ready)
- Policy-as-code with signed rule bundles
- Fail-closed defaults

## 3.2 Core Components

1. API Gateway Layer
- AuthN/AuthZ (JWT/mTLS/internal service auth)
- Strict request validation and rate limits
- Idempotency key support

2. Orchestrator Service
- Deterministic pipeline state machine
- Runtime guardrails (timeout/entity/chunk limits)
- Retry and compensating actions

3. Domain Engines
- Extraction engine
- Classification engine
- Fusion engine
- Policy decision engine
- Redaction engine

4. Control Plane
- Rule bundle registry
- Rule versioning and rollout strategy
- Feature flags and kill switches

5. Data Plane
- Object storage for uploads/artifacts
- Audit event stream
- Metrics + traces + logs correlation

## 3.3 Current Bootstrap in Repo

Initial v2 bootstrap is now added:

- core/v2/settings.py: runtime safety controls
- core/v2/models.py: orchestration output contracts
- core/v2/ports.py: strict engine interfaces
- core/v2/pipeline.py: deterministic orchestrator shell with guardrails
- core/v2/adapters/legacy.py: compatibility bridge for v1 agents

## 4) v2 Delivery Plan (Phased)

## Phase A: Foundation Hardening (Week 1-2)

1. Extract all v1 side effects behind ports/adapters.
2. Introduce rule bundle versioning and immutable activation IDs.
3. Add secure archive extraction controls:
- path traversal prevention
- extraction size ceilings
- file count limits
- depth limits
4. Introduce structured logging schema (trace_id, document_id, policy_version, decision_id).
5. Add deterministic idempotency handling in API.

Exit criteria:
- All pipeline operations available through v2 orchestrator path.
- No direct agent coupling from API layer.

## Phase B: Async Production Pipeline (Week 3-4)

1. Add durable job queue (RQ/Celery/Arq/Kafka-backed workers).
2. Convert analyze endpoint into submit + status + result retrieval pattern.
3. Persist pipeline state transitions.
4. Add dead-letter queue and replay tooling.

Exit criteria:
- Safe handling of workload spikes without API saturation.
- Retries are isolated per stage.

## Phase C: Security and Compliance (Week 4-6)

1. Upload validation pipeline:
- MIME + magic-byte validation
- malware scanner integration
- max content limits by file class
2. Secrets management hardening (no plaintext secrets in env for production).
3. Signed policy bundles and verification at load time.
4. Tamper-evident audit chain for policy decisions.

Exit criteria:
- Threat model controls mapped to implementation and tests.
- Compliance evidence artifacts generated automatically.

## Phase D: Reliability and Operability (Week 6-8)

1. OpenTelemetry tracing end-to-end.
2. SLOs and dashboards:
- p95 latency
- error budget burn
- policy engine failure rate
3. Canary rollout for policy changes.
4. Chaos testing for worker/API/store dependencies.

Exit criteria:
- SLOs established and observed under load test.
- Incident playbooks and runbooks validated.

## Phase E: Verification and Release Gate (Week 8+)

1. Full CI matrix:
- unit
- contract
- integration
- e2e
- load
- security scans
2. SBOM + dependency and license scans.
3. Release gate policy:
- no critical vulnerabilities
- minimum coverage thresholds
- performance floor

Exit criteria:
- v2 GA readiness review.

## 5) Production Readiness Checklist (Must Pass)

1. Security
- OWASP ASVS controls mapped
- file handling abuse tests passing
- signed policy validation active

2. Reliability
- retry policy tested
- backpressure verified
- timeout and fail-closed behavior proven

3. Governance
- policy version traceability complete
- decision lineage exportable per trace_id

4. Operations
- dashboards and alerts active
- on-call runbooks complete
- rollback procedure tested

## 6) Immediate Engineering Backlog (Next 10 Work Items)

1. Wire v2 orchestrator into a shadow execution path from API.
2. Add secure archive extraction utility and replace direct tar/zip extractall usage.
3. Add idempotency key model and request dedupe store.
4. Add policy bundle manifest with hash/signature fields.
5. Add structured event emitter for audit trail.
6. Add contract tests around ports and adapters.
7. Add API response model for async job lifecycle.
8. Add worker process skeleton and queue adapter.
9. Add OpenTelemetry instrumentation entrypoints.
10. Add release gate script for CI enforcement.

## 7) Non-Negotiable Engineering Policies for v2

1. No direct domain logic in API handlers.
2. No unchecked filesystem extraction operations.
3. No policy rule execution without version and signature metadata.
4. No release without passing security and load gates.
5. Fail closed on pipeline safety limit violations.
