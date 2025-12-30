# Neuro-Semantic Rule Language (NSRL)

NSRL is the policy engine configuration for NDRA-PII. It defines **HOW** the system reacts to detected PII.

## Directory Structure
- **`rules/`**: The core logic files (YAML).
    - `financial.yml`: PCI-DSS, Banking rules.
    - `gov_id.yml`: SSN, Passport rules.
    - `gdpr.yml`: EU jurisdiction logic.
    - `escalation.yml`: Logical combinations (Toxic Combinations).
- **`contracts/`**: Schema definitions for Input/Output data integrity.
- **`meta/`**: Governance metadata (Change logs, Approvals).
- **`spec/`**: Formal language specification for NSRL.
