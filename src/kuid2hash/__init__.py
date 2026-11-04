"""Kuid2Hash - Trainz KUID to hex/hash converter."""

from .converter import compute_hash, convert_hex, hex_to_kuid, kuid_to_hex, rev_kuid

__version__ = "3.0"

__all__ = [
    "__version__",
    "hex_to_kuid",
    "kuid_to_hex",
    "compute_hash",
    "convert_hex",
    "rev_kuid",
]
