import sys
import os

sys.path.append(os.path.abspath("."))

try:
    from ndrapiicli import run_interactive
    print("CLI imported successfully.")
except ImportError as e:
    print(f"CLI import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"CLI import failed with error: {e}")
    sys.exit(1)
