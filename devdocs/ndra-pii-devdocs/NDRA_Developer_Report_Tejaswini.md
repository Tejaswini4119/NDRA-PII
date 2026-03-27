# NDRA-PII Developer Report
**Developer:** Tejaswini  
**Project:** Neuro-Semantic Distributed Risk Analysis for Personally Identifiable Information (NDRA-PII)  
**Date:** December 19, 2025  
**Current Phase:** Phase 3 Complete (Ready for Phase 4 Fusion)

---

## 1. Executive Summary
This report documents the architectural implementation of the NDRA-PII system. As of today, the system has successfully evolved from a conceptual design into a functional **Multi-Model Intelligence Platform**. We have established a strictly governed, agentic pipeline capable of ingesting diverse enterprise data, ensuring cryptographic integrity, and performing high-precision PII detection with granular location mapping.

## 2. System Architecture Implemented

The system follows a **Deterministic Multi-Agent Architecture** where each agent has a single, isolated responsibility.

### 2.1 Core Infrastructure (`core/`, `schemas/`)
- **Strict Typing**: Implemented Pydantic models (`DocumentMetadata`, `SemanticChunk`, `DetectedPII`) to enforce data consistency across agents.
- **Immutable Audit**: The `AuditAgent` (`agents/audit.py`) is active, recording every system event (Upload, Extraction, Detection) with **SHA-256 cryptographic chaining**. This ensures that the reasoning history is tamper-evident.
- **Service Layer**: A `FastAPI` application (`main.py`) serves as the entry point, supporting `multipart/form-data` uploads and real-time analysis.

### 2.2 Perception Layer: `ExtractorAgent` (`agents/extractor.py`)
We moved beyond basic PDF parsing to a robust **Multi-Model Ingestion Engine**.
- **Supported Formats**:
    - **Documents**: PDF, DOCX, PPTX.
    - **Data**: XLSX, CSV, JSON, XML, YAML.
    - **Communication**: EML, MSG.
    - **Web**: HTML.
    - **Archives**: ZIP, TAR.
- **Key Features**:
    - **Integrity**: Every file is SHA-256 hashed upon entry.
    - **Semantic Chunking**: Text is split into sliding windows (e.g., 500 tokens) respecting sentence boundaries to preserve context for NLP.
    - **Quarantine**: Files with unsupported MIME types are safely isolated to a `/quarantine` directory.

### 2.3 Cognition Layer: `ClassifierAgent` (`agents/classifier.py`)
This is the "Brain" of the PII detection capability.
- **Engine**: Integrated **Microsoft Presidio** using the **Spacy `en_core_web_lg`** (Large) model for superior Named Entity Recognition (NER).
- **Custom Recognizers**: Added specific regex patterns for Indian Context (**Aadhaar**, **PAN**) alongside standard US/Global entities.
- **Granular Mapping** (New Feature):
    - The system now maps every detected PII entity to its **Exact Location**.
    - **Output Example**: `Page 32 [Offset 450:461]`.
    - **Context**: Captures a "snippet" of text around the PII for explainability.

### 2.4 Interfaces
- **REST API**: endpoints (`/analyze/upload`) for integration.
- **CLI Tool**: `ndrapiicli.py` for rapid, local testing without server overhead.

---

## 3. Verification & Testing status

| Test Suite | Scope | Status | Result |
| :--- | :--- | :--- | :--- |
| `test_phase2.py` | PDF Ingestion & Hashing | **PASS** | Validated SHA-256 & Chunking |
| `test_real_pdf.py` | Real Document Extraction | **PASS** | Processed `Testing_Set.pdf` |
| `test_phase3_real.py` | PII Detection (PDF) | **PASS** | Found SSNs, Credit Cards, Emails |
| `test_multi_model.py` | Excel/JSON Ingestion | **PASS** | Processed `Testing_Set.xlsx` |
| `test_excel_pii.py` | Detailed Excel Mapping | **PASS** | **971 PII Entities** mapped with offsets |

---

## 4. Next Steps (Development Plan)

We are now transitioning from **"Observation"** (Seeing PII) to **"Governance"** (Acting on PII).

### Phase 4: PII Fusion (Immediate)
- **Goal**: Clean duplicate detections (e.g., overlapping spans).
- **Architecture**: A logic layer within `ClassifierAgent` to merge Entities based on score and span.

### Phase 5: Governance (NSRL)
- **Goal**: Make decisions.
- **Mechanism**: **Policy Agent** (`agents/policy.py`).
- **Input**: `ClassifiedChunk`.
- **Logic**: Neuro-Symbolic Rule Layer (YAML Rules).
    - *Example*: `IF entity="Aadhaar" THEN action="Redact"`.

### Phase 6: Redaction
- **Goal**: Enforcement.
- **Mechanism**: `Presidio Anonymizer` to mask text at the identified offsets.

---

**Report Status**: Complete  
**Signed**: NDRA-PII Agent
