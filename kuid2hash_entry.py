"""PyInstaller entry point: launches the Kuid2Hash app (GUI or CLI)."""

import sys

from kuid2hash.cli import main

if __name__ == "__main__":
    sys.exit(main())
