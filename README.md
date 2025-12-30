# NDRA-PII: Neuro-Semantic Distributed Risk Analysis for PII

**Enterprise-Grade Privacy Intelligence System**

[![Status](https://img.shields.io/badge/Status-Operational-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

## Overview

NDRA-PII is an advanced multi-agent system designed to automatically **detect**, **evaluate**, and **redact** Personally Identifiable Information (PII) from unstructured documents. Unlike simple regex tools, NDRA-PII employs a **Neuro-Semantic** approach, combining NLP signals with rigorous, logic-based **governance policies (NSRL)** to determine the risk level of every detected entity before taking action.

## Key Features

- **Multi-Agent Architecture**: Specialized agents for Extraction, Classification, Fusion, Policy, and Redaction.
- **NSRL Policy Engine**: Configurable YAML-based rules (e.g., "Redact US SSN if High Severity").
- **Smart Redaction**: Re-flows documents to strictly mask sensitive data while preserving context.
- **Audit Trails**: Full decision lineage for compliance (GDPR, HIPAA, PCI-DSS).

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
python ndrapiicli.py
```
1.  Enter the path to your file (e.g., `datasets/Testing_Set.pdf`).
2.  The system will process the file through all agents.
3.  The result will be saved in `output/` as `filename_redacted.pdf`.

### Usage (API)
Start the server:
```bash
python main.py
```
POST to `http://localhost:8000/analyze/upload`.

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

