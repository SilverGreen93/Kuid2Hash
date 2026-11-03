"""PyInstaller entry point: launches the Kuid2Hash app (GUI or CLI).

When built as a windowed (GUI-subsystem) exe, no console is attached by
default, so double-clicking the exe opens the GUI without a terminal
flash.  In CLI mode (arguments present) we attach a console and re-point
stdout/stderr so the conversion result is visible:

  * launched from an existing terminal → inherits its console (no-op)
  * launched without a console → AttachConsole(-1) allocates a new one
"""

import sys

if __name__ == "__main__":
    if sys.argv[1:]:
        if sys.platform == "win32":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # AttachConsole(-1) creates a new console when none exists.
            # When a console is already attached (inherited from the parent
            # shell) it fails with ERROR_ACCESS_DENIED; the inherited
            # console is then used as-is.
            kernel32.AttachConsole(-1)

    from kuid2hash.cli import main

    sys.exit(main())
