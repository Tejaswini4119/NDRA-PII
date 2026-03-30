# NDRA-PII: Neuro-Semantic Distributed Risk Analysis for PII

**Enterprise-Grade Privacy Intelligence System**

[![Status](https://img.shields.io/badge/Status-Operational-darkgreen)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/License-GPLv3-red)](LICENSE)

## Overview

NDRA-PII is an advanced multi-agent system designed to automatically **detect**, **evaluate**, and **redact** Personally Identifiable Information (PII) from unstructured documents. Unlike simple regex tools, NDRA-PII employs a **Neuro-Semantic** approach, combining NLP signals with rigorous, logic-based **governance policies (NSRL)** to determine the risk level of every detected entity before taking action.

## Key Features

- **Multi-Agent Architecture**: Specialized agents for Extraction, Classification, Fusion, Policy, and Redaction.
- **NSRL Policy Engine**: Configurable YAML-based rules (e.g., "Redact US SSN if High Severity").
- **Smart Redaction**: Re-flows documents to strictly mask sensitive data while preserving context.
- **Audit Trails**: Full decision lineage for compliance (GDPR, HIPAA, PCI-DSS).
- **Frozen Production Mode**: Defaults to verified end-to-end ingestion paths only, with experimental handlers disabled.

## Frozen Runtime Defaults

The system now defaults to a "working-set freeze" for predictable production behavior:

- `FREEZE_WORKING_SYSTEM=true` (default)
- `ENABLE_EXPERIMENTAL_INGESTION=false` (default)

When frozen, NDRA accepts only verified MIME families and quarantines unsupported/experimental inputs.
Experimental ingestion paths (archive recursion, image metadata-only handling, and MSG parsing) are opt-in and remain disabled unless explicitly enabled.

## Architecture

The system operates as a linear pipeline:

1.  **Ingestion Agent**: Reads PDF, DOCX, TXT.
2.  **Classifier Agent**: Detects PII (Presidio + Spacy + Regex).
3.  **Fusion Agent**: Merges overlapping entities (e.g., "New York" vs "New York City").
4.  **Policy Agent**: Applies NSRL rules to assign Risk Scores and Actions.
5.  **Redaction Agent**: Executes "Redact" actions.
6.  **Output**: Generates sanitized documents (`_redacted.pdf`).

## Directory Structure

| Directory | Description |
| :--- | :--- |
| `agents/` | Core logic for all autonomous agents. |
| `config/` | System configuration and architectural constraints. |
| `nsrl/` | **Neuro-Semantic Rule Language** definitions (Rules, Specs). |
| `schemas/` | Pydantic data models for strict type safety. |
| `datasets/`| Test data for benchmarking. |
| `tests/` | Unit and integration test suite. |
| `reports/` | Generated implementation and audit reports. |

## Quick Start

### Prerequisites
- Python 3.10+
- `pip`

### Installation
```bash
git clone https://github.com/Tejaswini4119/NDRA-PII.git
cd NDRA
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### Usage (CLI)
The most interactive way to use NDRA-PII is the CLI:

```bash
python -m ndra_stack.cli
```
1.  Enter the path to your file (e.g., `datasets/Testing_Set.pdf`).
2.  The system will process the file through all agents.
3.  The result will be saved in `output/` as `filename_redacted.pdf`.

### Usage (API)
Start the server:
```bash
python -m ndra_stack
```
POST to `http://localhost:8001/analyze/upload`.

## Packaged Layout

- `ndra_stack/`: packaged entrypoints (`api.py`, `cli.py`, `__main__.py`)
- `main.py`: legacy API module retained for backward compatibility
- `ndrapiicli.py`: legacy CLI module retained for backward compatibility
- `webui/`: static Web UI served at `/ui`

## Containerized Deployment (Phase 7 - Stage 1)

### Prerequisites
- Docker Desktop (or Docker Engine + Compose plugin)
- Ports available: `8001`, `9090`, `3000`

### One-Time Setup
```bash
cp .env.example .env
```

PowerShell:
```powershell
Copy-Item .env.example .env
```

### Build and Run
```bash
docker compose build api
docker compose up -d
```

## Single-Container Run (One `docker run`)

The project can be run end-to-end in a single container (API + Web UI + internal Prometheus for native charts):

```bash
docker build -t ndra-stack:allinone .

# If your build host has intermittent Docker DNS failures:
docker build --network=host -t ndra-stack:allinone .

docker run --rm -p 8001:8001 -p 9090:9090 \
  -v "$PWD/uploads:/app/uploads" \
  -v "$PWD/output:/app/output" \
  -v "$PWD/quarantine:/app/quarantine" \
  -v "$PWD/artifacts:/app/artifacts" \
  -v "$PWD/audit:/app/audit" \
  --name ndra-stack ndra-stack:allinone
```

Endpoints:

- API: `http://localhost:8001/`
- Web UI: `http://localhost:8001/ui`
- Metrics: `http://localhost:8001/metrics`
- Internal Prometheus: `http://localhost:9090/targets`

### Validate Services
```bash
docker compose ps
```

- API health: `http://localhost:8001/`
- API metrics: `http://localhost:8001/metrics`
- Prometheus: `http://localhost:9090/targets`
- Grafana: `http://localhost:3000/`

### Runtime Volumes
- `./uploads` -> `/app/uploads`
- `./output` -> `/app/output`
- `./quarantine` -> `/app/quarantine`
- `./artifacts` -> `/app/artifacts`
- `./audit` -> `/app/audit`

### Stop Stack
```bash
docker compose down
```

## Policy Configuration (NSRL)
Policies are defined in `nsrl/rules/`. Example Rule:

```yaml
id: "FIN-PCI-CC-HIGH-001"
meta:
  name: "Credit Card High Risk"
  priority: 100
conditions:
  - type: "PII_TYPE"
    operator: "EQUALS"
    value: "CREDIT_CARD"
actions:
  classification: "RESTRICTED"
  severity: "CRITICAL"
  score: 1.0
  justification: "PCI-DSS mandated protection."
```

## Running Tests
```bash
python -m unittest discover tests
```

## Authors
- **Tejaswini** - *Lead, Applied Intelligence & Data Semantics Engineer - NDRA Intelligence Systems*
- **Pardhu Sree Rushi Varma** - *Core Architecture, Security & Governance Engineer - NDRA Governance Systems*
- **Rupa Yeshvitha Karedla** -  *Dataset Management & Preprocessing Engineer - NDRA Data-Pipelines*

