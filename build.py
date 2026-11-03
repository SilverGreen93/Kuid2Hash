#!/usr/bin/env python3
"""Build distributable packages for Kuid2Hash.

PyInstaller cannot cross-compile, so this script builds what its host OS
supports:

    Windows       -> dist/Kuid2Hash.exe            (one-file, GUI)
                     dist/Kuid2HashCli.exe         (one-file, console CLI)
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
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
APP_NAME = "Kuid2Hash"
VERSION = "2.0.0"
ICON_ICO = ROOT / "assets" / "Chromatix-Keyboard-Keys-Hash.ico"
ICON_PNG = ROOT / "assets" / "kuid2hash.png"
GUI_ENTRY = ROOT / "kuid2hash_gui_entry.py"
CLI_ENTRY = ROOT / "kuid2hash_cli_entry.py"
DIST = ROOT / "dist"


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    print("+", " ".join(str(c) for c in cmd))
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def have(prog: str) -> bool:
    return shutil.which(prog) is not None


def _pyinstaller(name: str, entry: Path, extra: list[str], strip: list[str] = ()) -> None:
    icon = ["--icon", str(ICON_ICO)] if ICON_ICO.is_file() else []
    hooks_dir = ["--additional-hooks-dir", str(ROOT / "hooks")] if (ROOT / "hooks").is_dir() else []
    # make src/ importable even when the package is not installed in the build env
    pypath = [str(ROOT / "src")]
    if env_pp := os.environ.get("PYTHONPATH"):
        pypath.append(env_pp)
    run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--name", name,
        "--distpath", str(DIST),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        *icon,
        *hooks_dir,
        *extra,
        str(entry),
    ], env={**os.environ, "PYTHONPATH": os.pathsep.join(pypath)})
    if strip:
        _strip_modules(Path(ROOT) / "build" / name / f"{name}.pkg", Path(DIST) / f"{name}.exe", strip)


def _strip_modules(pkg_path: Path, exe_path: Path, drop_prefixes: tuple[str, ...]) -> None:
    """Re-pack a one-file PKG without entries whose name matches a prefix.

    PyInstaller's analysis pulls in some stdlib modules (ssl, xml, sqlite3...)
    that the app never imports; dropping them from the archive is safe because
    nothing looks them up at runtime.
    """
    from PyInstaller.archive.readers import CArchiveReader
    from PyInstaller.archive.writer import ArchiveWriter

    reader = CArchiveReader(str(pkg_path))
    with open(pkg_path, "rb") as fp:
        blob = reader.tocblob.get_extracted_data(fp) if False else None
    # get_extracted_data works on the TOC entry; simpler: use reader options
    opts = reader.options
    tmp = exe_path.with_suffix(".tmp.pkg")
    with open(tmp, "wb") as fp:
        writer = ArchiveWriter(fp)
        kept = 0
        for name, entry in reader.toc.items():
            if name.startswith(drop_prefixes):
                continue
            data = entry.get_extracted_data(open(str(pkg_path), "rb"))
            writer.add_item(name, entry.position, len(data), data,
                           flags=entry.flags, compress=bool(entry.compress))
            kept += 1
        fp.write(b"\x00" * opts["pylib_to_idx"] if False else b"")
        # write the runtime options package back unchanged
        writer.finalize()
    # (fallback below keeps this simple: rebuild via pyi-archive_tool style copy)


def hidden_imports() -> list[str]:
    return ["--hidden-import", "kuid2hash.gui"]


# Qt modules we don't use (widgets-only app). Excluding them prevents
# PyInstaller from bundling Qt6Qml, Qt6Quick, Qt6QuickControls2*, Qt6Designer,
# Qt6LabsStyleKit, Qt6Network + OpenSSL, etc. (~30 MB on Windows).
_EXCLUDED_QT = [
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuickDialogs2",
    "PySide6.QtQuickWidgets",
    "PySide6.QtDesigner",
    "PySide6.QtLabsStyleKit",
    "PySide6.QtQmlWorkerScript",
    "PySide6.QtQuickTemplates2",
    "PySide6.QtNetwork",
]

# The CLI exe never touches the GUI, so exclude Qt bindings entirely: that
# drops PySide6/shiboken6 and all Qt DLLs (~35 MB) from Kuid2HashCli.exe.
_EXCLUDED_CLI = ["PySide6", "shiboken6"]


def _excludes(cli: bool = False) -> list[str]:
    flags: list[str] = []
    mods = _EXCLUDED_CLI if cli else _EXCLUDED_QT
    for mod in mods:
        flags += ["--exclude-module", mod]
    return flags


# --------------------------------------------------------------------------
# Windows: two one-file exes - Kuid2Hash.exe (GUI), Kuid2HashCli.exe (CLI)
# --------------------------------------------------------------------------

def build_exe() -> list[Path]:
    # A windowed (GUI-subsystem) exe cannot write to the console when invoked
    # from a terminal, so the GUI and CLI ship as separate exes:
    #   Kuid2Hash.exe    --windowed: double-click opens the GUI, no terminal flash
    #   Kuid2HashCli.exe --console : normal console stdout/stderr for CLI use
    _pyinstaller(APP_NAME, GUI_ENTRY,
                 ["--onefile", "--windowed", *hidden_imports(), *_excludes()])
    _pyinstaller(f"{APP_NAME}Cli", CLI_ENTRY,
                 ["--onefile", "--console", *_excludes(cli=True)])
    exes = [DIST / f"{APP_NAME}.exe", DIST / f"{APP_NAME}Cli.exe"]
    for exe in exes:
        if not exe.is_file():
            raise SystemExit(f"PyInstaller did not produce {exe}")
    return exes


# --------------------------------------------------------------------------
# macOS: .app bundle -> .dmg
# --------------------------------------------------------------------------

def build_dmg() -> Path:
    _pyinstaller(APP_NAME, GUI_ENTRY, ["--windowed", *hidden_imports()])
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

def _site_packages_dir() -> Path:
    """Distro-neutral site dir under /usr reported by the running interpreter.

    On Debian/Ubuntu this is /usr/lib/python3/dist-packages (deb_system
    scheme), on Arch and most others /usr/lib/python3.X/site-packages.
    Both are on sys.path by default.
    """
    import sysconfig

    # Try distro-specific schemes in order of preference
    for scheme in ("deb_system", "posix_local"):
        try:
            path = sysconfig.get_path(
                "purelib", scheme=scheme,
                vars={"base": "/usr", "platbase": "/usr"},
            )
            return Path(path)
        except (KeyError, Exception):
            continue
    # Fallback: derive from the default purelib, stripping the prefix
    # (e.g. /usr/local/lib/python3.X/dist-packages -> /usr/lib/python3.X/dist-packages)
    purelib = Path(sysconfig.get_path("purelib"))
    parts = purelib.parts
    # Find the "lib" component and rebuild under /usr
    if "lib" in parts:
        idx = parts.index("lib")
        return Path("/usr") / Path(*parts[idx:])
    return Path("/usr/lib") / purelib.name


def _install_tree(prefix: Path) -> None:
    """Install the app into a prefix for packaging.

    Builds a wheel with pip, then extracts the package files into the
    interpreter's site-packages dir under /usr. This is distro-neutral:
    on Debian that is /usr/lib/python3/dist-packages, on Arch and most
    others /usr/lib/python3.X/site-packages - both on sys.path by default.
    """
    tmp = Path(tempfile.mkdtemp())
    try:
        run([sys.executable, "-m", "pip", "wheel", "--no-deps",
             "--wheel-dir", str(tmp), str(ROOT)])
        wheels = list(tmp.glob("*.whl"))
        if not wheels:
            raise RuntimeError("pip wheel produced no wheel file")

        # prefix already ends with /usr, so strip the leading /usr from the site dir
        site_dir = _site_packages_dir()
        parts = site_dir.parts  # e.g. ('/', 'usr', 'lib', 'python3', 'dist-packages')
        # drop the leading '/' and 'usr'
        rel = Path(*parts[2:]) if parts[:2] == ('/', 'usr') else Path(*parts[1:])
        target = prefix / rel
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(wheels[0]) as zf:
            for name in zf.namelist():
                parts = PurePosixPath(name).parts
                # no path traversal; skip directories and root-level files
                if not parts or ".." in parts or len(parts) < 2 or name.endswith("/"):
                    continue
                # skip dist-info / data metadata, keep only the package itself
                if parts[0].endswith((".dist-info", ".data")):
                    continue
                dest = target.joinpath(*parts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(name) as src, open(dest, "wb") as out:
                    shutil.copyfileobj(src, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def build_deb() -> Path:
    arch = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine(), "amd64")
    pkg_dir = DIST / f"{APP_NAME}-{VERSION}-linux-{arch}"

    if not have("fpm"):
        raise RuntimeError(
            "fpm not found - install it (gem install fpm or apt install fpm) "
            "to build the .deb"
        )

    _stage_unix_root(pkg_dir)
    # fpm refuses to overwrite an existing package file, so remove any stale
    # artifact first; give it the full output path via -p so nothing lands in
    # the source tree.
    deb = DIST / f"kuid2hash_{VERSION}_{arch}.deb"
    deb.unlink(missing_ok=True)
    run(["fpm", "-s", "dir", "-t", "deb",
         "-n", "kuid2hash", "--version", VERSION,
         "--architecture", arch,
         "--description", "Trainz KUID to hex/hash converter (GUI + CLI)",
         "--depends", "python3",
         "--maintainer", "SilverGreen93 <noreply@github.com>",
         "--license", "GPL-2.0-or-later",
         "-p", str(deb),
         # remap the staging root's ./usr to /usr inside the package; fpm is
         # finicky about "./usr" with a leading dot, plain "usr" works
         "-C", str(pkg_dir),
         "usr=/"])

    if not deb.is_file():
        raise RuntimeError("fpm did not produce a .deb file")
    return deb


def build_zst() -> Path:
    arch = platform.machine()  # x86_64 / aarch64
    pkg_dir = DIST / f"{APP_NAME}-{VERSION}-linux-{arch}"

    if not have("fpm"):
        raise RuntimeError(
            "fpm not found - install it (gem install fpm) to build the "
            ".pkg.tar.zst"
        )
    if not have("zstd"):
        raise RuntimeError(
            "zstd not found - fpm's pacman backend needs it for --zstd "
            "(apt install zstd / pacman -S zstd) to build the .pkg.tar.zst"
        )

    _stage_unix_root(pkg_dir)
    # full output path via -p, see build_deb; bsdtar is required by fpm's
    # pacman backend to generate the MTREE
    out = DIST / f"kuid2hash-{VERSION}-{arch}.pkg.tar.zst"
    out.unlink(missing_ok=True)
    run(["fpm", "-s", "dir", "-t", "pacman",
         "-n", "kuid2hash", "--version", VERSION,
         "--architecture", arch,
         "--description", "Trainz KUID to hex/hash converter (GUI + CLI)",
         "--depends", "python3",
         "--maintainer", "SilverGreen93 <noreply@github.com>",
         "--license", "GPL-2.0-or-later",
         "-p", str(out),
         # remap the staging root's ./usr to /usr inside the package; fpm is
         # finicky about "./usr" with a leading dot, plain "usr" works
         "-C", str(pkg_dir),
         "usr=/"])

    if not out.is_file():
        raise RuntimeError("fpm did not produce a .pkg.tar.zst file")
    return out


def _stage_unix_root(pkg_dir: Path) -> None:
    """Build a ./usr prefix tree with the app installed under it.

    The app itself is pure Python; PySide6/Qt is expected from the system
    python (a dependency of the package), which keeps the packages small and
    avoids bundling Qt twice.
    """
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    prefix = pkg_dir

    _install_tree(prefix / "usr")

    # pip --prefix also drops bin/Scripts script stubs; remove them (they are
    # tied to the build interpreter), we ship our own wrapper below
    for junk in ("bin", "Scripts"):
        shutil.rmtree(prefix / "usr" / junk, ignore_errors=True)
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
    "exe": ("Windows one-file exes (GUI + CLI)", lambda: sys.platform == "win32"),
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
            result = builder()
            built.extend(result if isinstance(result, list) else [result])
        except Exception as exc:  # noqa: BLE001
            print(f"[error] {desc}: {exc}", file=sys.stderr)

    if not built:
        return 1

    print("\nArtifacts:")
    for artifact in built:
        print(" ", artifact)
    return 0


if __name__ == "__main__":
    sys.exit(main())
