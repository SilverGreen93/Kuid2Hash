"""Smoke tests for the PySide6 GUI (offscreen).

Skipped automatically when no Qt binding is installed. These verify the same
behaviour as the WinForms original: two-way live conversion driven only by the
focused field, hash updates, reverse-kuid handling, and invalid input keeping
the last valid values.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtWidgets import QApplication  # noqa: E402

from kuid2hash.gui import KuidWindow  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def window(qapp):
    w = KuidWindow()
    w.show()
    qapp.processEvents()  # realize the window so focus works
    return w


def test_initial_values(window):
    assert window.kuid_edit.text() == "<kuid2:474195:123456:1>"
    assert window.hex_edit.text() == "53 3C 07 02 40 E2 01 00"
    assert window.hash_edit.text() == "hash-CB"


def test_kuid_field_drives_hex_and_hash(window):
    window.kuid_edit.setFocus()
    window.kuid_edit.setText("kuid 68787 1097")
    assert window.hex_edit.text() == "B3 0C 01 00 49 04 00 00"
    assert window.hash_edit.text() == "hash-F3"


def test_hex_field_drives_kuid_and_hash(window):
    window.hex_edit.setFocus()
    window.hex_edit.setText("39 02 00 00")
    assert window.kuid_edit.text() == "<kuid:-1:569>"
    assert window.hash_edit.text() == "hash-3B"


def test_reverse_checkbox_reverses_hex(window):
    # set up an 8 byte kuid without triggering the checkbox logic; focus the
    # hex field so typing drives conversion (same as a user), then toggle
    window.reverse_check.blockSignals(True)
    window.reverse_check.setChecked(False)
    window.reverse_check.blockSignals(False)

    window.hex_edit.setFocus()
    window.hex_edit.setText("B3 0C 01 00 49 04 00 00")
    assert window.kuid_edit.text() == "<kuid:68787:1097>"

    # the toggle itself must fire even when neither text field is focused,
    # exactly like the WinForms original
    window.clearFocus()
    QApplication.instance().processEvents()

    window.reverse_check.setChecked(True)
    assert window.hex_edit.text() == "49 04 00 00 B3 0C 01 00"


def test_reverse_checkbox_no_effect_on_uid_minus_one(window):
    # a uid -1 kuid is only 4 bytes; toggling reverse must not touch it
    window.reverse_check.blockSignals(True)
    window.reverse_check.setChecked(False)
    window.reverse_check.blockSignals(False)

    window.hex_edit.setFocus()
    window.hex_edit.setText("39 02 00 00")

    window.clearFocus()
    QApplication.instance().processEvents()

    window.reverse_check.setChecked(True)
    assert window.hex_edit.text() == "39 02 00 00"


def test_invalid_input_keeps_last_valid_values(window):
    window.kuid_edit.setFocus()
    window.kuid_edit.setText("kuid 68787 1097")
    hex_before = window.hex_edit.text()
    hash_before = window.hash_edit.text()

    window.kuid_edit.setText("garbage")
    assert window.hex_edit.text() == hex_before
    assert window.hash_edit.text() == hash_before


def test_unfocused_updates_do_not_drive_conversion(window):
    # give the kuid field focus, then move it away; edits made while no field
    # is focused must not trigger the live conversion, mirroring the WinForms
    # "If txtKuid.Focused" guard
    window.kuid_edit.setFocus()
    window.hex_edit.setFocus()  # leave the kuid field unfocused
    window.kuid_edit.setText("kuid 68787 1097")
    assert window.hex_edit.text() == "53 3C 07 02 40 E2 01 00"
