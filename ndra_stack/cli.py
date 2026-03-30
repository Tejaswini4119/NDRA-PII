"""Packaged CLI entrypoint for NDRA-PII."""

from ndrapiicli import run_interactive


def main() -> None:
    """Run the interactive CLI."""
    run_interactive()


if __name__ == "__main__":
    main()
