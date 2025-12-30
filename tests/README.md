# Tests

This directory contains the automated test suite for the NDRA-PII system.

## Running Tests
Run all tests via:
```bash
python -m unittest discover tests
```

## Test Modules
- **`test_fusion.py`**: Verifies entity deduplication logic.
- **`test_policy.py`**: Verifies NSRL rule evaluation and risk scoring.
- **`test_redaction.py`**: Verifies correct text replacement and masking.
- **`expectations/`**: Contains "Golden Files" for regression testing.
