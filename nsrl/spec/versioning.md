# NSRL Versioning Policy

## Semantic Versioning
Rules follow SemVer `MAJOR.MINOR.PATCH` semantics.

*   **MAJOR**: Breaking change (e.g., changes logic behavior, removes fields).
*   **MINOR**: Backward-compatible addition (e.g., adding a new condition).
*   **PATCH**: Backward-compatible fix (e.g., typo in description).

## Rule Deprecation
Rules can be marked as `deprecated: true`. They will continue to run but emit warnings in the audit log.
