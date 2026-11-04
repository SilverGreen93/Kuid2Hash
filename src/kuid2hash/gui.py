"""PySide6 GUI for Kuid2Hash.

Port of frmKuid (WinForms): two-way live conversion between the KUID string
and its hex bytes, plus the hash and a "Reverse kuid" checkbox. Only the
focused field drives updates; invalid input while typing is ignored and the
last valid values are kept.
"""

from __future__ import annotations

import sys
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from pathlib import Path

from .converter import compute_hash, convert_hex, hex_to_kuid, kuid_to_hex, rev_kuid

__all__ = ["KuidWindow", "run_gui"]

_ASSET_DIR = Path(__file__).resolve().parent.parent.parent / "assets"


def _resource_path(name: str) -> str | None:
    """Absolute path to a bundled resource (works from source and PyInstaller)."""
    if getattr(sys, "frozen", False):  # running under PyInstaller
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / name
    else:
        base = _ASSET_DIR / name
    return str(base) if base.is_file() else None

APP_TITLE = "Kuid2Hash v2.0"
GITHUB_URL = "https://github.com/SilverGreen93/Kuid2Hash"
ICON_FILE = "Chromatix-Keyboard-Keys-Hash.ico"


def _to_hex(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def _window_icon() -> QIcon | None:
    """The app icon, if it can be found next to the code or in the bundle.

    Setting it on the application as well as the window is what puts it in the
    Windows taskbar; --icon alone only stamps the exe file on disk.
    """
    path = _resource_path(ICON_FILE)
    return QIcon(path) if path else None


class KuidWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._updating = False
        self._build()        # initial values, mirroring the WinForms designer defaults
        self.kuid_edit.setText("<kuid2:474195:123456:1>")
        self.hex_edit.setText("53 3C 07 02 40 E2 01 00")
        self.hash_edit.setText("hash-CB")

    def _build(self) -> None:
        self.setWindowTitle(APP_TITLE)
        icon = _window_icon()
        if icon:
            self.setWindowIcon(icon)

        bold = QFont()
        bold.setBold(True)
        bold.setPointSize(10)
        small = QFont()
        small.setPointSize(8)

        form = QVBoxLayout(self)
        form.setContentsMargins(12, 10, 12, 8)
        form.setSpacing(8)

        # one grid so the labels share a column and every line edit starts at
        # the same x; column 1 is how wide a full kuid2 string needs, column 2
        # absorbs whatever extra the window has, so the edits never stretch
        fields = QGridLayout()
        fields.setSpacing(8)
        fields.setColumnStretch(1, 0)
        fields.setColumnStretch(2, 1)

        self.kuid_edit = QLineEdit()
        self.hex_edit = QLineEdit()
        self.hex_edit.setMaxLength(24)
        self.hash_edit = QLineEdit()
        self.hash_edit.setReadOnly(True)

        self.reverse_check = QCheckBox("Reverse kuid")
        self.reverse_check.setFont(QFont(self.font().family(), 10))

        # how wide each box needs to be: the kuid/hex edits must fit the
        # longest value we display, a full kuid2 string. The hash is only ever
        # "hash-XX", so its box is half that width; it also has to leave room
        # for the reverse checkbox sharing its row, and can never be wider than
        # the edits column minus the checkbox and the gap between them
        fm = QFontMetrics(bold)
        edit_min = fm.horizontalAdvance("<kuid2:474195:123456:1>") + 50
        check_min = self.reverse_check.minimumSizeHint().width()
        hash_min = min(edit_min // 2, edit_min - check_min - fields.spacing())

        for r, (label_text, edit) in enumerate(
            (("KUID:", self.kuid_edit), ("HEX:", self.hex_edit))
        ):
            label = QLabel(label_text)
            label.setFont(bold)
            edit.setFont(bold)
            edit.setMinimumWidth(edit_min)
            fields.addWidget(label, r, 0)
            fields.addWidget(edit, r, 1)

        # the hash row holds a short box, left aligned, and the reverse
        # checkbox at the right edge of the edits column; the box needs its
        # width as both a minimum and a maximum, otherwise the cell stretches
        # it back out and it ends up underneath the checkbox
        hash_label = QLabel("HASH:")
        hash_label.setFont(bold)
        self.hash_edit.setFont(bold)
        self.hash_edit.setMinimumWidth(hash_min)
        self.hash_edit.setMaximumWidth(hash_min)
        fields.addWidget(hash_label, 2, 0)
        fields.addWidget(self.hash_edit, 2, 1, Qt.AlignmentFlag.AlignLeft)
        fields.addWidget(self.reverse_check, 2, 1, Qt.AlignmentFlag.AlignRight)
        form.addLayout(fields)

        # the credit and the repo link share one row, credit at the left edge
        # and link at the right, which saves a row of height
        footer = QHBoxLayout()
        credit = QLabel("SilverGreen93 (c) 2026")
        credit.setFont(small)
        link_text = "GitHub"
        link = QLabel(f'<a href="{GITHUB_URL}">{link_text}</a>')
        link.setFont(small)
        link.setOpenExternalLinks(False)
        link.linkActivated.connect(lambda: webbrowser.open(GITHUB_URL))
        footer.addWidget(credit)
        footer.addStretch(1)
        footer.addWidget(link)
        form.addLayout(footer)

        self.kuid_edit.textChanged.connect(self._on_kuid_changed)
        self.hex_edit.textChanged.connect(self._on_hex_changed)
        self.reverse_check.toggled.connect(self._on_reverse_toggled)

        # size the window to its content instead of hardcoded dimensions; a
        # fixed height keeps the layout spacings from stretching apart
        hint = self.sizeHint().expandedTo(self.minimumSizeHint())
        self.setFixedSize(hint)

    # -- behaviour ---------------------------------------------------------

    def _on_kuid_changed(self, text: str) -> None:
        if self.kuid_edit.hasFocus() and not self._updating:
            try:
                kuid_bytes = kuid_to_hex(text)
            except Exception:
                # ignore transient/invalid input while typing; keep last values
                return
            self._updating = True
            try:
                self.hash_edit.setText(f"hash-{compute_hash(kuid_bytes):02X}")
                if len(kuid_bytes) == 4:
                    # uid -1 kuid drops the FF FF FF FF user part; the Reverse
                    # kuid checkbox has no effect on it
                    self.hex_edit.setText(_to_hex(kuid_bytes))
                elif self.reverse_check.isChecked():
                    self.hex_edit.setText(_to_hex(rev_kuid(kuid_bytes)))
                else:
                    self.hex_edit.setText(_to_hex(kuid_bytes))
            finally:
                self._updating = False

    def _on_hex_changed(self, text: str) -> None:
        if self.hex_edit.hasFocus() and not self._updating:
            try:
                hex_bytes = convert_hex(text)
                # a 4 byte input is a uid -1 kuid; Reverse kuid has no effect
                if self.reverse_check.isChecked() and len(hex_bytes) == 8:
                    hex_bytes = rev_kuid(hex_bytes)
                kuid_str = hex_to_kuid(hex_bytes)
                hash_val = compute_hash(kuid_to_hex(kuid_str))
            except Exception:
                return
            self._updating = True
            try:
                self.kuid_edit.setText(kuid_str)
                self.hash_edit.setText(f"hash-{hash_val:02X}")
            finally:
                self._updating = False

    def _on_reverse_toggled(self, _checked: bool) -> None:
        if self._updating:
            return
        try:
            hex_bytes = convert_hex(self.hex_edit.text())
        except Exception:
            return
        # a 4 byte input is a uid -1 kuid; the checkbox has no effect on it
        if len(hex_bytes) == 8:
            self._updating = True
            try:
                self.hex_edit.setText(_to_hex(rev_kuid(hex_bytes)))
            finally:
                self._updating = False


def run_gui() -> int:
    """Launch the GUI. Returns the process exit code."""
    app = QApplication(sys.argv[:1])
    icon = _window_icon()
    if icon:
        app.setWindowIcon(icon)
    window = KuidWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())
