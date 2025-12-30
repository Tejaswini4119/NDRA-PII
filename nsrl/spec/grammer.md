# NSRL Grammar & Syntax Specification

NSRL rules are defined in **YAML** files. Each file represents a policy module containing a list of rules.

## Rule Structure

A single Rule Object has the following fields:

```yaml
id: "RULE-UNIQUE-ID-001"          # Unique identifier (string)
version: "1.0"                    # Rule version
meta:                             # Metadata for governance
  name: "Rule Name"
  description: "Human-readable description"
  author: "Author Name/ID"
  tags: ["compliance", "gdpr"]
  priority: 100                   # Execution priority (higher = overrides lower)

conditions:                       # Logical predicates required for rule to fire
  - type: "PII_MATCH"             # Logic type (PII_MATCH, METADATA_MATCH, CONTEXT_MATCH)
    field: "type"
    operator: "EQUALS"
    value: "US_SSN"

actions:                          # Interpretive outputs if conditions match
  score: 0.9                      # Sensitivity score (0.0 - 1.0)
  classification: "CONFIDENTIAL"  # Data classification label
  tags: ["pii", "restricted"]
  justification: "Contains US Social Security Number."
```

## Logic Operators

*   `EQUALS`
*   `NOT_EQUALS`
*   `CONTAINS`
*   `STARTS_WITH`
*   `ENDS_WITH`
*   `IN_LIST`
*   `GREATER_THAN`
*   `LESS_THAN`

## Composite Logic
Conditions in the top-level list are implicitly **AND**. Complex logic can be nested (not implemented in v1.0, flat AND lists preferred).
