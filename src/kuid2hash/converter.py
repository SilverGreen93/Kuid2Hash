"""Pure kuid conversion and hashing logic, decoupled from any UI.

Direct port of KuidConverter.vb. All functions are free of GUI dependencies,
so they can be reused by the CLI entry point, the GUI, and the test suite.
"""

from __future__ import annotations

import re

__all__ = [
    "hex_to_kuid",
    "kuid_to_hex",
    "compute_hash",
    "convert_hex",
    "rev_kuid",
]


def _le_int32(data: bytes) -> int:
    """Little-endian signed 32-bit integer from 4 bytes (BitConverter.ToInt32)."""
    return int.from_bytes(data, "little", signed=True)


def _int32_le(value: int) -> bytearray:
    """Signed 32-bit integer to little-endian bytes (BitConverter.GetBytes)."""
    return bytearray(value.to_bytes(4, "little", signed=True))


def hex_to_kuid(kuid: bytes) -> str:
    """Translate a binary kuid to its string form (e.g. "<kuid2:68787:1097:2>").

    :param kuid: 8-byte kuid, or 4 bytes for a uid -1 kuid (content id only)
    :returns: the kuid as a bracketed string
    """
    if not isinstance(kuid, (bytes, bytearray)) or len(kuid) not in (4, 8):
        raise ValueError(
            "kuid must contain exactly 8 bytes, or 4 bytes for a uid -1 kuid."
        )

    rstring = "<kuid"

    # a 4 byte input is the content id of a uid -1 kuid (the FF FF FF FF user
    # part is implicit)
    if len(kuid) == 4:
        cbytes = bytearray(kuid)
        u_int = -1
        version = 0
    else:
        ubytes = bytearray(kuid[0:4])
        cbytes = bytearray(kuid[4:8])

        if ubytes[3] & (1 << 0):
            # negative user id, ignore version
            version = 0
        else:
            version = ubytes[3] >> 1
            ubytes[3] &= 0x01

        u_int = _le_int32(bytes(ubytes))

    # a uid of -1 (FF FF FF FF) is still printed with its user part: "<kuid:-1:...>"

    rstring += "2:" if version != 0 else ":"
    rstring += f"{u_int}:{_le_int32(bytes(cbytes))}"

    if version != 0:
        rstring += f":{version}"

    rstring += ">"
    return rstring


def kuid_to_hex(kuid: str) -> bytes:
    """Translate a kuid string (e.g. "kuid 68787 1097", "<kuid2:68787:1097:3>",
    or "<kuid:-1:1097>") to its binary form.

    :param kuid: the kuid as string
    :returns: 8 bytes (4 user + 4 content), or only the 4 content id bytes
        when the uid is -1
    """
    if not isinstance(kuid, str) or kuid == "":
        raise ValueError("kuid must not be empty.")

    # strip any surrounding angle brackets emitted by hex_to_kuid (e.g. "<kuid2:...>")
    # VB's Trim("<"c, ">"c) removes leading/trailing < and > characters in any mix
    kuid = kuid.strip("<")
    while kuid.endswith(">"):
        kuid = kuid[:-1]
    kuid = kuid.strip()

    # split on colons and/or whitespace so both "kuid:68787:1097" and
    # "kuid 68787 1097" are accepted
    tokens = [t for t in re.split(r"[:\s]+", kuid) if t]

    if len(tokens) < 3:
        raise ValueError(
            "Invalid kuid: expected at least 'kuid uid cid' (e.g. '<kuid:-1:1097>')."
        )

    # parse the numeric parts (skip the leading tag) and convert to integers
    num = [0, 0, 0]
    upper = 3 if len(tokens) > 4 else len(tokens) - 1
    for i in range(1, upper + 1):
        try:
            # .NET Integer.TryParse accepts a leading +/-; Python int() does too
            num[i - 1] = int(tokens[i], 10)
        except ValueError:
            raise ValueError(f"Invalid kuid part: '{tokens[i]}'.") from None

    # get the bytes from integers (uid -1 is FF FF FF FF)
    ubytes = _int32_le(num[0])
    cbytes = _int32_le(num[1])
    if 0 < num[2] < 128 and num[0] >= 0:  # check if uid is negative
        # add the version number to byte 4 of uid
        ubytes[3] ^= (num[2] << 1) & 0xFF

    # a uid of -1 drops the FF FF FF FF user part: only the content id bytes
    # are returned
    if num[0] == -1:
        return bytes(cbytes)

    # merge bytes (always exactly 8: 4 user + 4 content)
    return bytes(ubytes) + bytes(cbytes)


def compute_hash(kuid: bytes) -> int:
    """Compute the hash of a kuid (xor of all bytes, with the version bit
    xored back out for positive 8-byte kuids).

    :param kuid: 8-byte kuid, or 4 bytes for a uid -1 kuid
    :returns: one byte - the hash code
    """
    if not isinstance(kuid, (bytes, bytearray)) or len(kuid) not in (4, 8):
        raise ValueError(
            "kuid must contain exactly 8 bytes, or 4 bytes for a uid -1 kuid."
        )

    h = 0

    # calculate hash using xor; a 4 byte input is the content id of a uid -1
    # kuid, whose implicit FF FF FF FF user part xors to zero and does not
    # affect the hash
    for i in range(len(kuid)):
        h ^= kuid[i]

    # version needs to be ignored, so xor that out, only if uid is positive
    # (8 byte kuids only)
    if len(kuid) == 8 and (kuid[3] & (1 << 0)) == 0:
        h ^= kuid[3]

    return h


def convert_hex(t: str) -> bytes:
    """Convert a hex string (space/dash/colon/comma separated) to a byte array.

    :param t: hex string, e.g. "B3 0C 01 00 49 04 00 00" or "39 02 00 00"
    :returns: 8 bytes (or 4 bytes for a uid -1 kuid)
    """
    if not isinstance(t, str) or t == "":
        raise ValueError("Hex string must not be empty.")

    s = [tok for tok in re.split(r"[ \-:,]+", t) if tok]

    # 4 bytes is the content id of a uid -1 kuid (the FF FF FF FF user part is implicit)
    if len(s) not in (4, 8):
        raise ValueError(
            "Expected exactly 8 hex bytes (or 4 for a uid -1 kuid), "
            f"got {len(s)}."
        )

    data = bytearray()
    for tok in s:
        try:
            data.append(int(tok, 16))
        except ValueError:
            raise ValueError(f"Invalid hex byte: '{tok}' in '{t}'.") from None
    return bytes(data)


def rev_kuid(kuid: bytes) -> bytes:
    """Reverse the UID with the CID (for map files):
    a-b-c-d-e-f-g-h -> e-f-g-h-a-b-c-d.

    :param kuid: 8-byte kuid
    :returns: the reversed 8-byte kuid
    """
    if not isinstance(kuid, (bytes, bytearray)) or len(kuid) != 8:
        raise ValueError("kuid must contain exactly 8 bytes.")

    return bytes(kuid[4:8]) + bytes(kuid[0:4])
