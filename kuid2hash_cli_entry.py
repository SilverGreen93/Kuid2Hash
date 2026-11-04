"""PyInstaller entry point for the CLI exe (Kuid2HashCli.exe).

Built with --console so stdout/stderr are attached to the terminal by
default.  With no arguments it prints usage and exits; use Kuid2Hash.exe
(GUI subsystem) for the GUI.
"""

import sys

if __name__ == "__main__":
    from kuid2hash.cli import main

    if not sys.argv[1:]:
        print('Usage: Kuid2HashCli.exe "<kuid2:474195:123456:1>"')
        print('       Kuid2HashCli.exe "53 3C 07 02 40 E2 01 00"')
        print('       Use Kuid2Hash.exe for the GUI.')
        sys.exit(1)

    sys.exit(main())
