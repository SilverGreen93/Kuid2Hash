"""Custom PyInstaller hook for PyQt6 (GUI build only).

Replaces the stock hook to skip collecting opengl32sw.dll (19.7 MB
software GL fallback) and ANGLE DLLs, which are not needed for a
Qt Widgets-only application. The CLI exe is built with --exclude-module
PyQt6 instead, so this hook never runs there.
"""
import os

from PyInstaller.utils.hooks.qt import (
    pyqt6_library_info,
    ensure_single_qt_bindings_package,
)

ensure_single_qt_bindings_package("PyQt6")

if pyqt6_library_info.version is not None:
    # same implicit imports the stock hook adds (sip is part of PyQt6)
    hiddenimports = ["PyQt6.sip", "pkgutil"]

    # Collect Qt binaries but skip opengl32sw.dll and ANGLE (libEGL/libGLESv2).
    # For a Widgets-only app these are unnecessary (saves ~20 MB on Windows).
    _skip = {"opengl32sw.dll", "libEGL.dll", "libGLESv2.dll"}
    all_binaries = pyqt6_library_info.collect_extra_binaries()
    binaries = [
        (src, dst) for src, dst in all_binaries
        if os.path.basename(src) not in _skip
    ]
