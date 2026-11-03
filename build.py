#!/usr/bin/env python3
"""Build distributable packages for Kuid2Hash.

PyInstaller cannot cross-compile, so this script builds what its host OS
supports:

    Windows       -> dist/Kuid2Hash.exe            (one-file, windowed)
    macOS         -> dist/Kuid2Hash-<ver>.dmg      (.app bundle + hdiutil)
    Linux (deb)   -> dist/kuid2hash_<ver>_amd64.deb   (needs fpm or dpkg)
    Linux (zst)   -> dist/kuid2hash-<ver>-x86_64.pkg.tar.zst (needs arch-package-build or pacman's package files via fpm)

Usage:
    python build.py            # build all artifacts available on this host
    python build.py --only exe|dmg|deb|zst   # build one artifact

The GitHub Actions workflow in .github/workflows/release.yml runs this script
on each OS in a matrix and uploads the results to the GitHub release.
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "Kuid2Hash"
VERSION = "2.0.0"
ICON_ICO = ROOT / "assets" / "Chromatix-Keyboard-Keys-Hash.ico"
ICON_PNG = ROOT / "assets" / "kuid2hash.png"
ENTRY = ROOT / "kuid2hash_entry.py"
DIST = ROOT / "dist"


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    print("+", " ".join(str(c) for c in cmd))
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def have(prog: str) -> bool:
    return shutil.which(prog) is not None


def _pyinstaller(name: str, extra: list[str]) -> None:
    icon = ["--icon", str(ICON_ICO)] if ICON_ICO.is_file() else []
    run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--name", name,
        "--distpath", str(DIST),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        *icon,
        *extra,
        str(ENTRY),
    ])


def hidden_imports() -> list[str]:
    return ["--hidden-import", "kuid2hash.gui"]


# --------------------------------------------------------------------------
# Windows: one-file hybrid exe (GUI when no args, CLI with args)
# --------------------------------------------------------------------------

def build_exe() -> Path:
    # NOTE: no --windowed here. The app is a hybrid: it shows the GUI when run
    # without arguments and prints to stdout in CLI mode. A windowed (GUI
    # subsystem) exe detaches stdout, which would break CLI use; the console
    # build keeps both working.
    _pyinstaller(APP_NAME, ["--onefile", *hidden_imports()])
    exe = DIST / f"{APP_NAME}.exe"
    if not exe.is_file():
        raise SystemExit(f"PyInstaller did not produce {exe}")
    return exe


# --------------------------------------------------------------------------
# macOS: .app bundle -> .dmg
# --------------------------------------------------------------------------

def build_dmg() -> Path:
    _pyinstaller(APP_NAME, ["--windowed", *hidden_imports()])
    app = DIST / f"{APP_NAME}.app"
    if not app.is_file() and not app.is_dir():
        raise SystemExit(f"PyInstaller did not produce {app}")

    dmg = DIST / f"{APP_NAME}-{VERSION}-macos.dmg"
    staging = Path(tempfile.mkdtemp())
    try:
        shutil.copytree(app, staging / APP_NAME + ".app")
        if ICON_PNG.is_file():
            # a simple background image for the dmg window
            shutil.copy(ICON_PNG, staging / "background.png")
        hdiutil = ["hdiutil", "create", "-volname", APP_NAME,
                   "-srcfolder", str(staging), "-ov", "-format", "UDZO", str(dmg)]
        run(hdiutil)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    if not dmg.is_file():
        raise SystemExit("hdiutil did not produce the dmg")
    return dmg


# --------------------------------------------------------------------------
# Linux: .deb and .pkg.tar.zst via fpm (fallbacks below)
# --------------------------------------------------------------------------

def _install_tree(prefix: Path) -> None:
    """Install the app into a prefix using pip, for packaging."""
    run([sys.executable, "-m", "pip", "install", "--prefix", str(prefix),
         "--no-deps", str(ROOT)])


def build_deb() -> Path:
    arch = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine(), "amd64")
    pkg_dir = DIST / f"{APP_NAME}-{VERSION}-linux-{arch}"

    if have("fpm"):
        _stage_unix_root(pkg_dir)
        run(["fpm", "-s", "dir", "-t", "deb",
             "-n", "kuid2hash", "--version", VERSION,
             "--architecture", arch,
             "--description", "Trainz KUID to hex/hash converter (GUI + CLI)",
             "--depends", "python3",
             "--maintainer", "SilverGreen93",
             "--license", "GPL-2.0-or-later",
             "-C", str(pkg_dir),
             "./usr=/usr"])
        deb = DIST / f"kuid2hash_{VERSION}_{arch}.deb"
        produced = sorted(DIST.glob(f"kuid2hash_*_{arch}.deb"))
        if produced:
            src = produced[-1]
            if src.resolve() != deb.resolve():
                shutil.move(str(src), deb)
            return deb

    raise SystemExit("fpm not found - install it (gem install fpm or apt install fpm) to build the .deb")


def build_zst() -> Path:
    arch = platform.machine()  # x86_64 / aarch64
    pkg_dir = DIST / f"{APP_NAME}-{VERSION}-linux-{arch}"

    if have("fpm"):
        _stage_unix_root(pkg_dir)
        run(["fpm", "-s", "dir", "-t", "pacman",
             "-n", "kuid2hash", "--version", VERSION,
             "--architecture", arch,
             "--description", "Trainz KUID to hex/hash converter (GUI + CLI)",
             "--depends", "python3",
             "--maintainer", "SilverGreen93 <noreply@github.com>",
             "--license", "GPL-2.0-or-later",
             "-C", str(pkg_dir),
             "./usr=/usr"])
        produced = sorted(DIST.glob(f"kuid2hash-{VERSION}-*.pkg.tar.zst"))
        if produced:
            return produced[-1]

    raise SystemExit("fpm not found - install it (gem install fpm or pacman -S ruby-fpm) to build the .pkg.tar.zst")


def _stage_unix_root(pkg_dir: Path) -> None:
    """Build a ./usr prefix tree with the app installed under it.

    The app itself is pure Python; PySide6/Qt is expected from the system
    python (a dependency of the package), which keeps the packages small and
    avoids bundling Qt twice.
    """
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    prefix = pkg_dir
    _install_tree(prefix)

    # pip --prefix also drops a bin/ at the prefix root; remove those windows
    # scripts, we ship our own wrapper below
    for junk in ("bin", "Scripts"):
        shutil.rmtree(prefix / junk, ignore_errors=True)

    # wrap the console script so PATH works without activating anything
    bindir = prefix / "usr" / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    wrapper = bindir / "kuid2hash"
    wrapper.write_text(
        "#!/bin/sh\nexec python3 -m kuid2hash.cli \"$@\"\n", newline="\n"
    )
    wrapper.chmod(0o755)

    # desktop entry for the GUI
    share = prefix / "usr" / "share"
    apps = share / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    (apps / "kuid2hash.desktop").write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Kuid2Hash\n"
        "Comment=Trainz KUID to hex/hash converter\n"
        "Exec=kuid2hash\n"
        "Icon=kuid2hash\n"
        "Categories=Utility;\n",
        newline="\n",
    )
    icons = share / "icons" / "hicolor" / "256x256" / "apps"
    icons.mkdir(parents=True, exist_ok=True)
    if ICON_PNG.is_file():
        shutil.copy(ICON_PNG, icons / "kuid2hash.png")


# --------------------------------------------------------------------------

BUILDERS = {
    "exe": ("Windows one-file exe", lambda: sys.platform == "win32"),
    "dmg": ("macOS dmg", lambda: sys.platform == "darwin"),
    "deb": ("Linux .deb (needs fpm)", lambda: sys.platform.startswith("linux")),
    "zst": ("Linux .pkg.tar.zst (needs fpm)", lambda: sys.platform.startswith("linux")),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=sorted(BUILDERS), help="build a single artifact")
    args = parser.parse_args()

    DIST.mkdir(exist_ok=True)
    targets = [args.only] if args.only else list(BUILDERS)
    built: list[Path] = []

    for target in targets:
        desc, supported = BUILDERS[target]
        if not supported():
            print(f"[skip] {desc}: not supported on this host ({platform.system()})")
            continue
        print(f"[build] {desc}")
        builder = {"exe": build_exe, "dmg": build_dmg,
                   "deb": build_deb, "zst": build_zst}[target]
        try:
            built.append(builder())
        except Exception as exc:  # noqa: BLE001
            print(f"[error] {desc}: {exc}", file=sys.stderr)

    if built:
        print("\nArtifacts:")
        for artifact in built:
            print(" ", artifact)
    return 0 if built or args.only is None else 1


if __name__ == "__main__":
    sys.exit(main())
