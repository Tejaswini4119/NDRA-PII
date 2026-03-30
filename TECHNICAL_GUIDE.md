# NDRA Stack Technical Guide

## 1) Purpose
This guide is the operational and technical reference for NDRA-PII (packaged as NDRA Stack).
It covers:
- Full feature inventory
- Architecture and processing flow
- All supported run modes
- CLI, API, and Web UI usage
- Redaction control modes and advanced options
- Observability and metrics
- Testing matrix and validation paths
- Troubleshooting and recovery playbooks

---

## 2) Project Structure (Current)
Primary runtime paths:
- `ndra_stack/`: packaged entrypoints
  - `ndra_stack/__main__.py` (default package run)
  - `ndra_stack/api.py` (API entrypoint)
  - `ndra_stack/cli.py` (CLI entrypoint)
- `main.py`: FastAPI app + full pipeline orchestration
- `ndrapiicli.py`: interactive CLI implementation
- `agents/`: extraction, classification, fusion, policy, redaction, audit
- `schemas/`: strict Pydantic domain models
- `nsrl/rules/`: policy rules (YAML)
- `config/settings.py`: runtime and security configuration
- `webui/index.html`: native, framework-free UI
- `docker/`: container startup scripts
- `config/prometheus.yml`, `config/prometheus.single.yml`: observability scraping configs

Backwards compatibility retained:
- Top-level modules remain usable while packaged entrypoints are the canonical run path.

---

## 3) Full Feature Inventory

### 3.1 Core Pipeline Features
1. Multi-agent orchestration pipeline:
   - Extractor -> Classifier -> Fusion -> Policy -> Redaction -> Audit
2. Ingestion and chunking:
   - Multi-format document parsing
   - Semantic chunking with overlap and sentence-boundary handling
3. PII detection:
   - Presidio-based recognizers
   - Confidence scoring and location spans
   - Additional custom recognizers (for regional IDs where defined)
4. Fusion:
   - Intra-chunk overlap deduplication
   - Cross-chunk entity stitching
5. NSRL governance:
   - Rule loading from YAML
   - Priority-based policy evaluation
   - Document-level context escalation (CONTEXT_MATCH rules)
6. Redaction:
   - Policy-driven redaction
   - Selective redaction by chosen entity types
   - Multiple mask styles
7. Audit and traceability:
   - Event logging with trace IDs
   - Tamper-evident hash-chain audit log and verification endpoint

### 3.2 API and Security Features
1. API endpoints:
   - Health
   - Upload analysis
   - Path analysis (gated)
   - Audit chain verification
2. Security hardening:
   - API key support (`X-API-Key`)
   - CORS allowlist
   - MIME allowlist
   - Upload size limit
   - Safe file path handling
3. Abuse protection:
   - Sliding-window per-IP rate limiting on `/analyze/*`

### 3.3 UI Features (Native + Performance Focused)
1. Dark minimal UI with no frontend framework
2. Upload + analyze workflow
3. Advanced controls:
   - Redaction mode (`policy`, `selected_types`)
   - Mask style (`entity`, `fixed`, `block`)
   - Findings limit
   - Show-only-redacted toggle
4. Results views:
   - KPI cards
   - Risk + trace summary
   - Pipeline viewer (stage timings)
   - Findings table
   - Native redacted document viewport
5. Observability section:
   - Native Prometheus charts
   - Proxy-backed metric querying through API

### 3.4 Observability Features
1. Prometheus metrics export at `/metrics`
2. Metric families:
   - `ndrapii_files_processed_total{status=...}`
   - `ndrapii_policy_actions_total{action=...,entity_type=...}`
3. UI proxy endpoints:
   - `/ops/prometheus/query`
   - `/ops/prometheus/query_range`
4. Prometheus target configurations for compose and single-container modes

### 3.5 Containerization Features
1. Compose mode:
   - API + Prometheus + Grafana services
2. Single-container mode (`ndra-stack:allinone`):
   - API + internal Prometheus in one container
   - UI and observability available without multi-service orchestration
3. Resilient image build:
   - Pip retry/backoff logic
   - spaCy model download retry/backoff
   - Host-network fallback build command for DNS-flaky hosts

### 3.6 Testing Coverage (Current Test Set)
- `test_phase1.py`: baseline config/schema/audit bootstrap checks
- `test_phase2.py`: extraction flow
- `test_phase3_real.py`: real document detection path
- `test_real_pdf.py`: real PDF extraction path
- `test_excel_pii.py`: Excel PII checks
- `test_multi_model.py`: multi-format ingestion checks
- `test_fusion.py`: entity dedup/fusion logic
- `test_policy.py`: rule matching + document-level context checks + audit chain checks
- `test_redaction.py`: masking behavior correctness
- `test_rfc_email_parser.py`: RFC email parse/reconstruct integrity
- `test_v2_orchestrator.py`: v2 orchestration safety behavior
- `validate_rfc_parser.py`, `verify_cli_load.py`, `verify_real_rules.py`: utility validation scripts

---

## 4) Architecture and Data Flow
1. Input arrives from API upload/path endpoint or CLI file path.
2. Extractor normalizes and chunks content.
3. Classifier detects entities and confidence spans.
4. Fusion resolves overlaps and boundary splits.
5. Policy engine applies NSRL rules and determines decisions.
6. Redaction applies policy and/or control-mode masking.
7. Output model includes:
   - Detection summaries
   - Policy traces
   - Document risk
   - Pipeline stage timings
   - Redacted document text
8. Audit events are recorded with trace IDs.

---

## 5) Run Modes (All Supported)

### 5.1 Packaged Local API (Recommended Dev)
```bash
python -m ndra_stack
```
Then open:
- `http://127.0.0.1:8001/`
- `http://127.0.0.1:8001/ui`

### 5.2 Packaged CLI
```bash
python -m ndra_stack.cli
```

### 5.3 Nix Development Shell
```bash
nix develop -c python -m ndra_stack
```

### 5.4 Docker Compose (Service Split)
```bash
docker compose up -d
```
Services:
- API on `8001`
- Prometheus on `9090`
- Grafana on `3000`

### 5.5 Single Container (All-in-One)
Build:
```bash
docker build -t ndra-stack:allinone .
```
DNS fallback build:
```bash
docker build --network=host -t ndra-stack:allinone .
```
Run:
```bash
docker run --rm \
  -p 8001:8001 \
  -p 9090:9090 \
  -v "$PWD/uploads:/app/uploads" \
  -v "$PWD/output:/app/output" \
  -v "$PWD/quarantine:/app/quarantine" \
  -v "$PWD/artifacts:/app/artifacts" \
  -v "$PWD/audit:/app/audit" \
  --name ndra-stack \
  ndra-stack:allinone
```

---

## 6) API Endpoints and Usage

### 6.1 Health
- `GET /`
- Returns system status and active agents.

### 6.2 Upload Analysis
- `POST /analyze/upload`
- Multipart form field: `file`
- Optional form controls:
  - `redact_mode`: `policy` or `selected_types`
  - `redact_types`: comma-separated entity types
  - `mask_style`: `entity`, `fixed`, `block`
  - `findings_limit`: integer (bounded)
  - `show_only_redacted`: boolean

Example:
```bash
curl -X POST http://127.0.0.1:8001/analyze/upload \
  -F 'file=@datasets/Testing_Set.pdf;type=application/pdf' \
  -F 'redact_mode=selected_types' \
  -F 'redact_types=EMAIL_ADDRESS,PHONE_NUMBER,US_SSN' \
  -F 'mask_style=fixed' \
  -F 'findings_limit=150' \
  -F 'show_only_redacted=true'
```

### 6.3 Local Path Analysis (Optional/Gated)
- `POST /analyze/path`
- Enabled only if `ALLOWED_PATH_PREFIXES` is configured.

### 6.4 Audit Chain Verification
- `GET /audit/verify`
- Returns chain integrity status (or 409 on failure).

### 6.5 Metrics
- `GET /metrics`

### 6.6 Observability Proxy Endpoints (UI)
- `GET /ops/config`
- `GET /ops/prometheus/query`
- `GET /ops/prometheus/query_range`

---

## 7) Web UI Usage (Operational)

### 7.1 Basic Flow
1. Open `/ui`
2. Choose file
3. Set optional controls
4. Analyze
5. Review:
   - KPIs
   - Risk + trace
   - Pipeline stage timings
   - Findings table
   - Redacted viewport

### 7.2 Advanced Redaction Scenarios
1. Policy strict mode:
   - `redact_mode=policy`, `mask_style=entity`
2. Selective compliance mode:
   - `redact_mode=selected_types`
   - `redact_types=EMAIL_ADDRESS,PHONE_NUMBER`
3. Demo-safe masking:
   - `mask_style=block`
4. Analyst-focused table:
   - enable `show_only_redacted`
   - raise/lower `findings_limit`

---

## 8) CLI Usage Patterns
1. Start interactive CLI:
```bash
python -m ndra_stack.cli
```
2. Provide file path
3. Observe per-chunk policy decisions
4. Redacted PDF output generated in `output/`

---

## 9) Configuration Reference
Main file: `config/settings.py`

Important runtime keys:
- `API_KEY`
- `CORS_ORIGINS`
- `MAX_UPLOAD_BYTES`
- `ALLOWED_UPLOAD_MIMES`
- `ALLOWED_PATH_PREFIXES`
- `RATE_LIMIT_PER_MINUTE`
- `FREEZE_WORKING_SYSTEM`
- `FROZEN_SUPPORTED_MIMES`
- `ENABLE_EXPERIMENTAL_INGESTION`

Operational recommendation:
- Keep `FREEZE_WORKING_SYSTEM=true` in production for deterministic behavior.

Archive ingestion note:
- `.zip`, `.tar`, and `.gz` uploads are considered experimental.
- To allow archive uploads, set:
   - `FREEZE_WORKING_SYSTEM=false`
   - `ENABLE_EXPERIMENTAL_INGESTION=true`

---

## 10) Observability and Dashboards

### 10.1 Prometheus Targets
Compose mode: configured in `config/prometheus.yml`
Single-container mode: configured in `config/prometheus.single.yml`

### 10.2 Core Metrics to Track
- Throughput:
  - `sum(rate(ndrapii_files_processed_total[5m]))`
- Redaction action velocity:
  - `sum(rate(ndrapii_policy_actions_total[5m]))`
- Status counts:
  - `sum by(status) (ndrapii_files_processed_total)`

### 10.3 Quick Checks
```bash
curl http://127.0.0.1:8001/metrics
curl http://127.0.0.1:9090/-/healthy
curl --get 'http://127.0.0.1:9090/api/v1/query' --data-urlencode 'query=ndrapii_files_processed_total'
```

---

## 11) End-to-End Usage Cases

### Case A: Standard Compliance Sweep
- Input: policy/regulatory PDF bundle
- Mode: `policy`
- Mask: `entity`
- Outcome: broad policy-based redaction with audit trace

### Case B: Targeted Contact Data Redaction
- Input: support/export records
- Mode: `selected_types`
- Types: `EMAIL_ADDRESS,PHONE_NUMBER`
- Mask: `fixed`
- Outcome: minimal redaction footprint with selected sensitivity classes

### Case C: Legal Review Artifact
- Input: mixed-format report
- Mode: `policy`
- Mask: `block`
- Limit: constrained findings for focused review
- Outcome: highly anonymized redacted viewport for legal sharing

### Case D: API Automation Pipeline
- Trigger: upstream process uploads files to `/analyze/upload`
- Capture: `trace_id`, `document_risk`, `policy_decisions`
- Observe: Prometheus counters and rates

### Case E: CLI-Only Operations
- Environment without browser access
- Interactive run through CLI
- Redacted PDF output consumed by downstream tools

---

## 12) Troubleshooting Playbook

### 12.1 UI Unreachable (`127.0.0.1:8001`)
1. Check container/process status
2. Check app logs for import/runtime errors
3. Confirm port bind and firewall availability

### 12.2 Docker Build DNS Failures
Symptoms:
- pip retries with name-resolution failures

Actions:
1. Use host-network build:
```bash
docker build --network=host -t ndra-stack:allinone .
```
2. Retry build (Dockerfile includes backoff loops)

### 12.3 Prometheus Charts Empty
1. Confirm API metrics endpoint is reachable
2. Verify target health in Prometheus `/targets`
3. Generate at least one analysis event
4. Refresh UI metrics panel

### 12.4 Path Analysis Forbidden
- Set `ALLOWED_PATH_PREFIXES` correctly
- Ensure requested path resolves under an allowed prefix

### 12.5 API 401 on Analyze/Audit
- Set or pass `X-API-Key` correctly

---

## 13) Validation Checklist (Release Readiness)
1. API health returns active
2. `/ui` loads and processes sample upload
3. Redacted viewport renders content
4. Pipeline timings visible
5. Prometheus target is `up`
6. `ndrapii_files_processed_total` increases after run
7. Audit verify endpoint passes
8. Frozen mode remains enabled for production

---

## 14) Canonical Commands (Quick Reference)

Local API:
```bash
python -m ndra_stack
```

Local CLI:
```bash
python -m ndra_stack.cli
```

Compose:
```bash
docker compose up -d
```

Single-container build/run:
```bash
docker build --network=host -t ndra-stack:allinone .

docker run --rm \
  -p 8001:8001 -p 9090:9090 \
  -v "$PWD/uploads:/app/uploads" \
  -v "$PWD/output:/app/output" \
  -v "$PWD/quarantine:/app/quarantine" \
  -v "$PWD/artifacts:/app/artifacts" \
  -v "$PWD/audit:/app/audit" \
  --name ndra-stack ndra-stack:allinone
```

---

## 15) Notes
- This guide reflects current runtime behavior and packaging conventions in this repository state.
- Legacy entry modules are retained for compatibility while packaged entrypoints are preferred.
