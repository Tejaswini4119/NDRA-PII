# NDRA-PII Architectural Review Report
**Reviewer:** Claude (AI Architectural Review)  
**Project:** Neuro-Semantic Distributed Risk Analysis for Personally Identifiable Information (NDRA-PII)  
**Date:** March 2026  
**Scope:** Full codebase review — security, architecture, production readiness

---

## 1. Executive Summary

The NDRA-PII platform has a well-structured multi-agent pipeline and a clear separation of concerns across its agents. However, several **critical security vulnerabilities** and **production-readiness gaps** were identified that must be addressed before deployment. This report documents each finding, its severity, and the remediation applied.

---

## 2. Critical Security Findings

### 2.1 Zip Slip / Tar Slip Vulnerability *(CRITICAL — FIXED)*

**File:** `agents/extractor.py` → `_process_archive()`  
**Finding:** The archive extraction logic called `z.extractall(temp_path)` and `t.extractall(temp_path)` without validating member paths first. A maliciously crafted ZIP or TAR file containing paths like `../../../etc/passwd` would extract files outside the intended temporary directory, potentially overwriting system files or the application itself.  
**Fix Applied:** Added pre-extraction path traversal validation for every archive member. Any archive containing a member whose resolved path escapes the extraction directory is rejected and quarantined.

### 2.2 Arbitrary File Read via `/analyze/path` *(HIGH — FIXED)*

**File:** `main.py`  
**Finding:** The `/analyze/path` endpoint accepted any server-side file path without restriction. Any authenticated (or, since there was no auth, unauthenticated) user could trigger analysis of any file accessible to the server process, including `/etc/passwd`, private keys, or other sensitive system files — constituting an arbitrary file-read vulnerability.  
**Fix Applied:** The endpoint is **disabled by default** (returns HTTP 403 when `ALLOWED_PATH_PREFIXES` is empty). When explicitly enabled, requests are validated against a configurable whitelist of absolute directory prefixes, and all paths are resolved to their canonical form before comparison to prevent `../` traversal.

### 2.3 Wildcard CORS Policy *(HIGH — FIXED)*

**File:** `main.py`  
**Finding:** `allow_origins=["*"]` was hardcoded, permitting any origin to make cross-origin requests to the API. For a system handling PII this is unacceptable — it enables Cross-Site Request Forgery (CSRF) and exposes the API to browser-based attacks from any website.  
**Fix Applied:** CORS origins are now controlled by the `CORS_ORIGINS` setting (defaults to `["http://localhost:3000"]`). The `allow_methods` and `allow_headers` values are also tightened to explicit allowlists.

### 2.4 Hardcoded Grafana Admin Password *(HIGH — FIXED)*

**File:** `docker-compose.yml`  
**Finding:** `GF_SECURITY_ADMIN_PASSWORD=admin` was hardcoded directly in the Compose file. Any deployment of this stack would expose the Grafana dashboard with a trivially guessable password.  
**Fix Applied:** The password is now sourced from an environment variable (`${GF_SECURITY_ADMIN_PASSWORD:-changeme}`), requiring operators to set it via `.env` or deployment secrets before production use.

---

## 3. Architectural Flaws

### 3.1 Duplicate Import in `main.py` *(LOW — FIXED)*

**Finding:** `from agents.audit import AuditAgent` appeared twice on consecutive lines, indicating a copy-paste error during development.  
**Fix Applied:** Duplicate import removed.

### 3.2 Audit Hash Chain Not Persistent *(MEDIUM — FIXED)*

**File:** `agents/audit.py`  
**Finding:** `self.last_hash = "0" * 64` was set unconditionally at construction time. Every server restart broke the cryptographic hash chain, invalidating the tamper-evidence property that the audit trail was designed to provide.  
**Fix Applied:** On startup the `AuditAgent` now reads the last recorded hash from the existing audit log file, resuming the chain. A fresh genesis hash is used only when no prior log exists.

### 3.3 File Quarantine Not Implemented *(MEDIUM — FIXED)*

**File:** `agents/extractor.py` → `_quarantine_file()`  
**Finding:** The actual file copy to the quarantine directory was commented out (`# shutil.copy(original_path, dest)`), meaning quarantined files were only logged but never actually isolated. Malicious files remained accessible in their original location.  
**Fix Applied:** `shutil.copy2()` is now called unconditionally to copy the file into the quarantine directory, with error handling if the copy fails.

### 3.4 `print()` Used Instead of Logger in `PolicyAgent` *(LOW — FIXED)*

**File:** `agents/policy_agent.py`  
**Finding:** Rule-loading progress was emitted via `print()` instead of the configured logger. This bypasses structured logging, log-level filtering, and any log-shipping infrastructure.  
**Fix Applied:** Replaced with `logger.info(...)`.

---

## 4. Production Readiness Gaps

### 4.1 No File Size Limit on Upload *(MEDIUM — FIXED)*

**File:** `main.py`  
**Finding:** The `/analyze/upload` endpoint had no size restriction. A malicious client could upload a multi-gigabyte file, causing out-of-memory conditions or disk exhaustion.  
**Fix Applied:** Uploads are now streamed in 64 KB chunks and aborted with HTTP 413 if the cumulative bytes exceed `MAX_UPLOAD_BYTES` (default 50 MB, configurable).

### 4.2 No MIME-Type Validation on Upload *(MEDIUM — FIXED)*

**File:** `main.py`  
**Finding:** The upload endpoint accepted any file type, including executable binaries, scripts, and other non-document formats. This unnecessarily increases the attack surface.  
**Fix Applied:** The `Content-Type` header is validated against a configurable `ALLOWED_UPLOAD_MIMES` whitelist. Requests with unlisted types are rejected with HTTP 415.

### 4.3 Unsafe Filename Handling in Upload *(MEDIUM — FIXED)*

**File:** `main.py`  
**Finding:** `file_location = f"{settings.UPLOAD_DIR}/{trace_id}_{file.filename}"` concatenated the user-supplied filename directly into a file path. A filename containing `/` or `..` could write files outside the upload directory.  
**Fix Applied:** `os.path.basename()` is applied to the client-supplied filename so only the leaf name component is used.

### 4.4 Missing Production Configuration Defaults *(LOW — FIXED)*

**File:** `config/settings.py`, `.env.example`  
**Finding:** Several security-relevant settings (`CORS_ORIGINS`, `MAX_UPLOAD_BYTES`, `ALLOWED_UPLOAD_MIMES`, `ALLOWED_PATH_PREFIXES`) were absent, forcing operators to accept insecure defaults or patch source code.  
**Fix Applied:** All settings are now declared in `NDRAConfig` with secure defaults and documented in `.env.example`.

---

## 5. Summary Table — Pass 1

| # | Severity | File | Finding | Status |
|---|----------|------|---------|--------|
| 1 | CRITICAL | `extractor.py` | Zip/Tar Slip path traversal in archive extraction | ✅ Fixed |
| 2 | HIGH | `main.py` | Arbitrary file-read via `/analyze/path` | ✅ Fixed |
| 3 | HIGH | `main.py` | Wildcard CORS (`allow_origins=["*"]`) | ✅ Fixed |
| 4 | HIGH | `docker-compose.yml` | Hardcoded Grafana admin password | ✅ Fixed |
| 5 | MEDIUM | `audit.py` | Hash chain resets to genesis on every restart | ✅ Fixed |
| 6 | MEDIUM | `extractor.py` | Quarantine implementation was no-op | ✅ Fixed |
| 7 | MEDIUM | `main.py` | No file size limit on upload | ✅ Fixed |
| 8 | MEDIUM | `main.py` | No MIME-type validation on upload | ✅ Fixed |
| 9 | MEDIUM | `main.py` | Unsafe user-supplied filename path construction | ✅ Fixed |
| 10 | LOW | `main.py` | Duplicate `AuditAgent` import | ✅ Fixed |
| 11 | LOW | `policy_agent.py` | `print()` instead of structured logger | ✅ Fixed |
| 12 | LOW | `settings.py` / `.env.example` | Missing security-relevant config options | ✅ Fixed |

---

## 6. Second-Pass Review Findings

A deeper review of the remaining codebase logic (agents, rules engine, async layer) revealed additional issues.

### 6.1 CONTEXT_MATCH Conditions Silently Always True *(CRITICAL — FIXED)*

**File:** `agents/policy_agent.py` → `_check_conditions()`  
**Finding:** The condition-evaluation loop only had a branch for `cond.type == "PII_MATCH"`. Any condition with `type == "CONTEXT_MATCH"` (including the high-priority escalation rules for density, toxic combinations, and jurisdiction) fell through the `if` block without returning `False`, causing the outer loop to complete and `return True`. As a result, **every escalation rule fired on every entity in every document**, forcibly classifying all PII as CRITICAL risk and triggering maximum-severity redaction regardless of actual document context.  
**Impact:** The `ESC-DENSITY-EXTREME-001` (priority 200), `ESC-TOXIC-ID-HEALTH-001` (priority 150), `ESC-TOXIC-ID-FIN-001` (priority 150), and `JUR-GDPR-001` (priority 150) rules — all of which are the **highest-priority rules in the system** — fired unconditionally, completely overriding the correctly calibrated `PII_MATCH` rules.  
**Fix Applied:** `CONTEXT_MATCH` conditions now explicitly return `False` at the entity level, with a clear code comment explaining that these rules require document-level evaluation that is out of scope for the per-entity `_check_conditions` method. An additional `else` clause returns `False` for any other unknown condition type.

### 6.2 Blocking Pipeline in Async FastAPI Handlers *(MEDIUM — FIXED)*

**File:** `main.py` → `analyze_file_upload()`, `analyze_local_path()`  
**Finding:** Both async endpoint handlers called `_run_pipeline()` — a fully synchronous, CPU and I/O bound function — directly without offloading to a thread pool. In FastAPI (Starlette), calling a blocking function from an `async def` handler blocks the underlying event loop, preventing all other concurrent requests from being processed until the pipeline completes. Under any meaningful load, this degrades to effectively single-threaded serial processing.  
**Fix Applied:** Both call sites now use `await asyncio.to_thread(_run_pipeline, ...)` to execute the blocking pipeline in a thread-pool thread, freeing the event loop for other requests.

### 6.3 `AuditAgent` Not Thread-Safe *(MEDIUM — FIXED)*

**File:** `agents/audit.py`  
**Finding:** `process()` read `self.last_hash`, computed a new hash based on it, updated `self.last_hash`, and then wrote to the log file — all without any synchronization. Under concurrent requests (which are now possible after Fix 6.2), two threads could read the same `last_hash` simultaneously, produce two entries both claiming the same `prev_hash`, and break the tamper-evident chain integrity.  
**Fix Applied:** A `threading.Lock()` is acquired for the entire hash-read → hash-compute → hash-store → file-write sequence, making the chain update atomic.

### 6.4 Unsafe `.decode()` on Potentially-`None` EML Payload *(LOW — FIXED)*

**File:** `agents/extractor.py` → `_read_eml()`  
**Finding:** `part.get_payload(decode=True).decode()` and `msg.get_payload(decode=True).decode()` would raise `AttributeError: 'NoneType' object has no attribute 'decode'` for EML messages whose payload is `None` (e.g., `multipart/mixed` container parts, `message/delivery-status`, or truncated messages). This would cause the extractor to silently quarantine valid email files.  
**Fix Applied:** Added null checks before each `.decode()` call and used `.decode(errors="replace")` to handle any encoding issues gracefully.

### 6.5 Unused Imports *(LOW — FIXED)*

**Files:** `main.py`, `ndrapiicli.py`  
**Finding:** `main.py` imported `shutil`, `BackgroundTasks`, and `Form` — none of which are used after the first-pass fixes. `ndrapiicli.py` imported `requests` which was never used (the CLI uses agents directly, not the HTTP API).  
**Fix Applied:** All four unused imports removed.

---

## 7. Summary Table — Pass 2

| # | Severity | File | Finding | Status |
|---|----------|------|---------|--------|
| 13 | CRITICAL | `policy_agent.py` | CONTEXT_MATCH conditions silently pass as True — escalation rules fire on all entities | ✅ Fixed |
| 14 | MEDIUM | `main.py` | Blocking `_run_pipeline` in async handlers starves event loop | ✅ Fixed |
| 15 | MEDIUM | `audit.py` | `last_hash` TOCTOU race condition under concurrent requests | ✅ Fixed |
| 16 | LOW | `extractor.py` | Unsafe `.decode()` on potentially-None EML payload | ✅ Fixed |
| 17 | LOW | `main.py` / `ndrapiicli.py` | Stale/unused imports | ✅ Fixed |

---

## 8. Recommended Next Steps (Version 2 Roadmap)

1. **Authentication & Authorization** — Add API-key or JWT-based authentication to all endpoints. The `/analyze/upload` and `/analyze/path` endpoints currently have no auth layer.
2. **Rate Limiting** — Integrate `slowapi` or an API gateway to prevent brute-force and denial-of-service attacks.
3. **Document-Level Escalation Rules** — Implement `evaluate_document()` in `PolicyAgent` to evaluate `CONTEXT_MATCH` rules (density, toxic combinations, jurisdiction) at the document level after all chunk-level processing is complete.
4. **OCR Integration** — The `_read_image()` stub (PaddleOCR TODO) should be completed to enable PII detection in scanned documents and images.
5. **Structured Logging / SIEM Export** — Replace `logging.basicConfig` with a JSON formatter (e.g., `python-json-logger`) so logs can be ingested by ELK, Splunk, or a cloud SIEM.
6. **Audit Log Integrity Verification** — Add a `/audit/verify` endpoint or offline CLI tool that walks the entire JSONL chain and confirms each `prev_hash` links correctly to the previous entry.
7. **Secrets Management** — Move API keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`) and the Grafana password out of `.env` files and into a secrets manager (HashiCorp Vault, AWS Secrets Manager, etc.) for production.
8. **Dependency Pinning** — `requirements.txt` uses unpinned package names. Pin all versions in `requirements.lock` and periodically audit for CVEs.

---

**Report Status:** Complete (Pass 1 + Pass 2)  
**Generated By:** Claude Architectural Review  
