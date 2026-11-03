"""Tests for the CLI behaviour (port of Program.vb semantics)."""

from kuid2hash.cli import is_hex_kuid, main, parse_kuid, run_cli


def test_parse_kuid_string_form():
    # explicit little-endian expectation: B3 0C 01 00 49 04 00 00
    assert parse_kuid("kuid 68787 1097") == bytes([0xB3, 0x0C, 0x01, 0x00, 0x49, 0x04, 0x00, 0x00])


def test_parse_kuid_hex_form():
    assert parse_kuid("B3 0C 01 00 49 04 00 00") == bytes(
        [0xB3, 0x0C, 0x01, 0x00, 0x49, 0x04, 0x00, 0x00]
    )


def test_parse_kuid_uid_minus_one():
    assert parse_kuid("kuid -1 569") == bytes([0x39, 0x02, 0x00, 0x00])
    assert parse_kuid("39 02 00 00") == bytes([0x39, 0x02, 0x00, 0x00])


def test_is_hex_kuid():
    assert is_hex_kuid("B3 0C 01 00 49 04 00 00")
    assert is_hex_kuid("39 02 00 00")
    assert is_hex_kuid("39-02-00-00")
    assert not is_hex_kuid("kuid 68787 1097")
    assert not is_hex_kuid("")


def test_run_cli_prints_expected_output(capsys):
    assert run_cli("kuid 68787 1097") is True
    out = capsys.readouterr().out.splitlines()
    assert out == [
        "kuid:  <kuid:68787:1097>",
        "hex:   B3 0C 01 00 49 04 00 00",
        "hash:  hash-F3",
    ]


def test_run_cli_error(capsys):
    assert run_cli("not a kuid") is False
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("Error:")


def test_main_with_args(capsys):
    assert main(["kuid2", "328583", "1373", "2"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "kuid:  <kuid2:328583:1373:2>"
    assert out[2] == "hash:  hash-D9"


def test_main_error_exit_code(capsys):
    assert main(["totally", "invalid"]) == 1
