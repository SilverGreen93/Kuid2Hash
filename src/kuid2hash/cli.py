"""Command line entry point.

With no arguments the GUI launches; with one or more arguments the app runs in
CLI mode and prints the converted kuid(s) and hash to stdout.

Port of Program.vb.
"""

from __future__ import annotations

import re
import sys

from .converter import compute_hash, convert_hex, hex_to_kuid, kuid_to_hex

__all__ = ["main", "run_cli", "parse_kuid", "is_hex_kuid"]


def main(argv: list[str] | None = None) -> int:
    """Entry point: no args -> GUI; args -> CLI conversion."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        try:
            from .gui import run_gui
        except ImportError:
            # distro packages ship the CLI as pure Python and expect the
            # system python to provide PyQt6; it may genuinely be missing
            print(
                "Error: the GUI needs PyQt6, which is not installed.\n"
                "Install it (pip install \"kuid2hash[gui]\", or your distro's\n"
                "python3-pyqt6 / python-pyqt6 package), or convert\n"
                "from the terminal: kuid2hash \"kuid 68787 1097\"",
                file=sys.stderr,
            )
            return 1

        return run_gui()

    # A single kuid may arrive as one quoted argument ("kuid 68787 1097") or,
    # if the shell split it, as several tokens. Re-join with spaces and treat
    # the whole thing as one kuid.
    joined = " ".join(argv)
    return 0 if run_cli(joined) else 1


def run_cli(arg: str) -> bool:
    """Process a single CLI argument (a kuid in string or binary form) and
    print the converted kuid, hex bytes and hash. Returns False (and prints to
    stderr) on error.
    """
    try:
        data = parse_kuid(arg)
    except Exception as exc:  # noqa: BLE001 - mirror VB's catch-all
        print(f"Error: {exc}", file=sys.stderr)
        return False

    print("kuid:  {}".format(hex_to_kuid(data)))
    print("hex:   {}".format(_to_hex(data)))
    print("hash:  hash-{:02X}".format(compute_hash(data)))
    return True


def parse_kuid(arg: str) -> bytes:
    """Detect whether the argument is a binary (hex) kuid or a string kuid and
    parse it.
    """
    trimmed = arg.strip()

    # binary format: only hex bytes (and separators) with 4 or 8 byte tokens
    if is_hex_kuid(trimmed):
        return convert_hex(trimmed)

    # otherwise treat as a string kuid ("kuid 68787 1097", "<kuid2:...>", etc.)
    return kuid_to_hex(trimmed)


def is_hex_kuid(arg: str) -> bool:
    """True when the argument looks like a hex byte sequence: splitting on the
    allowed separators yields 4 or 8 tokens, every one of them a valid hex byte.
    """
    s = [tok for tok in re.split(r"[ \-:,]+", arg) if tok]
    if len(s) not in (4, 8):
        return False

    for token in s:
        # a valid hex byte is 1-2 hex digits (Byte.TryParse with HexNumber)
        if not re.fullmatch(r"[0-9A-Fa-f]{1,2}", token):
            return False

    return True


def _to_hex(data: bytes) -> str:
    """Format bytes like BitConverter.ToString(...).Replace("-", " ")."""
    return " ".join(f"{b:02X}" for b in data)


if __name__ == "__main__":
    sys.exit(main())
