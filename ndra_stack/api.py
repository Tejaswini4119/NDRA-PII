"""Packaged API entrypoint for NDRA-PII."""

import uvicorn

from main import app


def main() -> None:
    """Run the NDRA API server."""
    uvicorn.run("ndra_stack.api:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()
