"""PyInstaller entry point for the GUI exe (Kuid2Hash.exe).

Built with --windowed (GUI subsystem) so double-clicking the exe opens the
GUI without a terminal flash.  Command line arguments are ignored; use
Kuid2HashCli.exe (console subsystem) for CLI mode.
"""

import sys

if __name__ == "__main__":
    from kuid2hash.gui import run_gui

    sys.exit(run_gui())
