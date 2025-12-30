# NDRA-PII Agents

This directory contains the autonomous agents that form the core processing pipeline of the Neuro-Semantic Distributed Risk Analysis system.

## Available Agents

### 1. `extractor.py` (Ingestion)
- **Role**: Ingests files (PDF, DOCX, TXT, etc.) and breaks them into semantic chunks.
- **Key Features**: Multi-format support, metadata extraction, offset tracking.

### 2. `classifier.py` (Detection)
- **Role**: Scans text chunks for Personally Identifiable Information (PII).
- **Tech Stack**: Microsoft Presidio, Spacy, Custom Regex.
- **Capabilities**: Detects 20+ entity types (SSN, Credit Card, Phone, Email, etc.).

### 3. `fusion_agent.py` (Resolution)
- **Role**: Deduplicates and merges overlapping PII entities.
- **Goal**: Ensures "John Doe" and "John" at the same location are treated as one accurate entity.

### 4. `policy_agent.py` (Governance)
- **Role**: Evaluates detected entities against NSRL Rules.
- **Input**: `ClassifiedChunk` + `nsrl/rules/*.yml`.
- **Output**: `GovernedChunk` with Actions (Redact/Allow) and Risk Scores.

### 5. `redaction_agent.py` (Enforcement)
- **Role**: Physically masks sensitive data in the text.
- **Action**: Replaces text with `[ENTITY_TYPE]` based on Policy decisions.

### 6. `audit.py` (Provenance)
- **Role**: Logs all major events and decisions for compliance auditing.
