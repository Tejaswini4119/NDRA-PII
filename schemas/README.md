# Schemas

This directory contains the Pydantic data models that strictly define the data structures flowing through the system.

## Key Models (`core_models.py`)
- **`DetectedPII`**: Describes a single entity found (text, type, score, location).
- **`ClassifiedChunk`**: A text chunk with a list of `DetectedPII`.
- **`GovernedChunk`**: A classified chunk enriched with Policy Decisions (Risk Score, Action).
- **`AgentDecision`**: The audit trace of *why* a decision was made.

## Rule Models (`rule_schema.py`)
- **`NSRLRule`**: Defines the structure of a YAML policy rule.
