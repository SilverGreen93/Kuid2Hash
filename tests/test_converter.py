"""Tests for kuid conversion logic, ported from KuidConversionTests.cs.

Validates the kuid conversions against a small CSV data set. For every row both
conversion directions are checked (string -> bytes and bytes -> string) as well
as the hash, which must be identical no matter which direction produced the byte
array.
"""

import re

import pytest

from kuid2hash.converter import (
    compute_hash,
    convert_hex,
    hex_to_kuid,
    kuid_to_hex,
    rev_kuid,
)

# StrKuid,BinKuid,Hash
CSV_DATA = """\
kuid 68787 1097,B3 0C 01 00 49 04 00 00,F3
kuid2 328583 1373 2,87 03 05 04 5D 05 00 00,D9
kuid2 146087 21661 127,A7 3A 02 FE 9D 54 00 00,56
kuid -2 1009,FE FF FF FF F1 03 00 00,F3
kuid 251996 -420662835,5C D8 03 00 CD 31 ED E6,70
kuid2 46819 15218 1,E3 B6 00 02 72 3B 00 00,1C
kuid -1 569,39 02 00 00,3B
kuid -1 100468,74 88 01 00,FD\
"""


def parse_csv(csv: str):
    """Parse the CSV data set into test rows."""
    rows = []
    for line in csv.splitlines():
        if not line:
            continue
        parts = line.split(",")
        assert len(parts) == 3, "CSV row must have exactly 3 columns: " + line
        rows.append((parts[0].strip(), parse_hex(parts[1]), int(parts[2].strip(), 16)))
    return rows


def parse_hex(hex_str: str) -> bytes:
    tokens = [t for t in re.split(r"[ \-:,]+", hex_str) if t]
    return bytes(int(t, 16) for t in tokens)


def to_hex(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


# String -> bytes: every kuid string must convert to exactly the binary form
# from the CSV. (For uid -1 kuids only the 4 content id bytes are expected, the
# FF FF FF FF user part is implicit.)
KUID_TO_HEX_CASES = [
    ("kuid 68787 1097", "B3 0C 01 00 49 04 00 00"),
    ("kuid2 328583 1373 2", "87 03 05 04 5D 05 00 00"),
    ("kuid2 146087 21661 127", "A7 3A 02 FE 9D 54 00 00"),
    ("kuid -2 1009", "FE FF FF FF F1 03 00 00"),
    ("kuid 251996 -420662835", "5C D8 03 00 CD 31 ED E6"),
    ("kuid2 46819 15218 1", "E3 B6 00 02 72 3B 00 00"),
    ("kuid -1 569", "39 02 00 00"),
    ("kuid -1 100468", "74 88 01 00"),
]


@pytest.mark.parametrize(("str_kuid", "expected_bin"), KUID_TO_HEX_CASES)
def test_kuid_to_hex_matches_expected_binary(str_kuid, expected_bin):
    actual = kuid_to_hex(str_kuid)
    assert to_hex(actual) == expected_bin, (
        f'kuid_to_hex("{str_kuid}") should be "{expected_bin}"'
    )


# Bytes -> string: every binary kuid from the CSV must convert back to a valid
# kuid string. The round-tripped string must parse again to exactly the same
# bytes (both directions work).
HEX_TO_KUID_CASES = [
    "B3 0C 01 00 49 04 00 00",
    "87 03 05 04 5D 05 00 00",
    "A7 3A 02 FE 9D 54 00 00",
    "FE FF FF FF F1 03 00 00",
    "5C D8 03 00 CD 31 ED E6",
    "E3 B6 00 02 72 3B 00 00",
    "39 02 00 00",
    "74 88 01 00",
]


@pytest.mark.parametrize("bin_kuid", HEX_TO_KUID_CASES)
def test_hex_to_kuid_round_trips_back_to_same_bytes(bin_kuid):
    data = parse_hex(bin_kuid)

    # direction: binary -> string (a uid -1 kuid is printed as "<kuid:-1:...>")
    str_kuid = hex_to_kuid(data)
    assert str_kuid.startswith("<kuid") and str_kuid.endswith(">"), (
        f'hex_to_kuid("{bin_kuid}") should return a bracketed kuid, got "{str_kuid}"'
    )

    # direction: string -> binary again must give exactly the same bytes back
    round_tripped = kuid_to_hex(str_kuid)
    assert data == round_tripped, (
        f'Round trip of "{bin_kuid}" via "{str_kuid}" should return the original bytes'
    )


COMPUTE_HASH_CASES = [
    ("kuid 68787 1097", "B3 0C 01 00 49 04 00 00", "F3"),
    ("kuid2 328583 1373 2", "87 03 05 04 5D 05 00 00", "D9"),
    ("kuid2 146087 21661 127", "A7 3A 02 FE 9D 54 00 00", "56"),
    ("kuid -2 1009", "FE FF FF FF F1 03 00 00", "F3"),
    ("kuid 251996 -420662835", "5C D8 03 00 CD 31 ED E6", "70"),
    ("kuid2 46819 15218 1", "E3 B6 00 02 72 3B 00 00", "1C"),
    ("kuid -1 569", "39 02 00 00", "3B"),
    ("kuid -1 100468", "74 88 01 00", "FD"),
]


@pytest.mark.parametrize(("str_kuid", "bin_kuid", "expected_hash"), COMPUTE_HASH_CASES)
def test_compute_hash_matches_expected_value(str_kuid, bin_kuid, expected_hash):
    from_string = kuid_to_hex(str_kuid)
    from_binary = parse_hex(bin_kuid)

    # both directions must produce the same byte array ...
    assert from_binary == from_string, (
        f'"{str_kuid}" and "{bin_kuid}" should be the same kuid'
    )

    # ... so the hash is identical either way and matches the CSV value
    expected = int(expected_hash, 16)
    assert compute_hash(from_string) == expected, (
        f'compute_hash("{str_kuid}") should be 0x{expected:02X}'
    )
    assert compute_hash(from_binary) == expected, (
        f'compute_hash("{bin_kuid}") should be 0x{expected:02X}'
    )


def test_csv_data_set_all_rows_convert_both_ways_and_hash_is_correct():
    rows = parse_csv(CSV_DATA)
    assert len(rows) == 8, "The CSV data set should contain 8 rows"

    for str_kuid, bin_kuid, row_hash in rows:
        # direction 1: string -> binary must equal the CSV column
        from_string = kuid_to_hex(str_kuid)
        assert bin_kuid == from_string, (
            f'Row "{str_kuid}": kuid_to_hex should return {to_hex(bin_kuid)}'
        )

        # direction 2: binary -> string must round-trip back to the same bytes
        str_form = hex_to_kuid(bin_kuid)
        assert bin_kuid == kuid_to_hex(str_form), (
            f'Row "{str_kuid}": hex_to_kuid returned "{str_form}" which does not '
            f"parse back to {to_hex(bin_kuid)}"
        )

        # hash must be correct from both directions
        assert compute_hash(from_string) == row_hash, (
            f'Row "{str_kuid}": hash of string-derived bytes should be 0x{row_hash:02X}'
        )
        assert compute_hash(bin_kuid) == row_hash, (
            f'Row "{str_kuid}": hash of binary-derived bytes should be 0x{row_hash:02X}'
        )


def test_uid_minus_one_is_printed_with_user_part():
    str_form = hex_to_kuid(parse_hex("39 02 00 00"))
    assert str_form == "<kuid:-1:569>"

    # the full 8 byte form must print identically (FF FF FF FF user part)
    str_full = hex_to_kuid(parse_hex("FF FF FF FF 39 02 00 00"))
    assert str_form == str_full


def test_convert_hex_accepts_all_separators():
    expected = bytes([0xB3, 0x0C, 0x01, 0x00, 0x49, 0x04, 0x00, 0x00])
    assert convert_hex("B3 0C 01 00 49 04 00 00") == expected
    assert convert_hex("b3-0c-01-00-49-04-00-00") == expected
    assert convert_hex("B3:0C:01:00:49:04:00:00") == expected
    assert convert_hex("B3, 0C, 01, 00, 49, 04, 00, 00") == expected


def test_convert_hex_rejects_bad_input():
    with pytest.raises(ValueError):
        convert_hex("")
    with pytest.raises(ValueError):
        convert_hex("B3 0C 01")            # wrong number of bytes
    with pytest.raises(ValueError):
        convert_hex("B3 0C ZZ 00 49 04 00 00")  # not a hex byte


def test_rev_kuid_swaps_uid_and_cid():
    data = parse_hex("B3 0C 01 00 49 04 00 00")
    assert rev_kuid(data) == parse_hex("49 04 00 00 B3 0C 01 00")
    # reversing twice is the identity
    assert rev_kuid(rev_kuid(data)) == data


def test_invalid_kuids_raise():
    with pytest.raises(ValueError):
        kuid_to_hex("")
    with pytest.raises(ValueError):
        kuid_to_hex("kuid 68787")          # missing content id
    with pytest.raises(ValueError):
        kuid_to_hex("kuid abc 1097")       # non numeric part
    with pytest.raises(ValueError):
        hex_to_kuid(b"\x01\x02")           # wrong byte count


def test_gui_default_values_round_trip():
    # the values shown in the WinForms designer must be a consistent kuid
    data = convert_hex("53 3C 07 02 40 E2 01 00")
    assert hex_to_kuid(data) == "<kuid2:474195:123456:1>"
    assert kuid_to_hex("<kuid2:474195:123456:1>") == data
    assert compute_hash(data) == 0xCB
