# Trainz Kuid2Hash

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/SilverGreen93/Kuid2Hash)](https://github.com/SilverGreen93/Kuid2Hash/releases/latest) [![Downloads (Latest Release)](https://img.shields.io/github/downloads/SilverGreen93/Kuid2Hash/latest/total?label=latest%20release%20downloads)](https://github.com/SilverGreen93/Kuid2Hash/releases/latest) ![GitHub all releases](https://img.shields.io/github/downloads/SilverGreen93/Kuid2Hash/total?label=total%20downloads)

This application helps you identify the folder in the Trainz Assets Database which holds a particular asset without using Content Manager.

![screenshot](assets/kuid2hash.png)

## Features

- Translates numeric KUIDs to hexadecimal
- Translates hexadecimal KUIDs to decimal
- Calculates the hash for a specific KUID -> Used to identify the directory in which a particular Trainz asset is stored

See more about the KUID Format Specification here: [KUID Format Specification](https://github.com/SilverGreen93/CDPExplorer/blob/master/kuid-format.md)

## Usage

The app runs as a GUI when started without arguments, and as a command line tool when arguments are given. From the repository root, run it without installing the package by adding `src` to Python's module search path:

```powershell
# Windows PowerShell
$env:PYTHONPATH = "src"
python -m kuid2hash.gui                    # starts the GUI
python -m kuid2hash.cli "kuid 68787 1097"  # runs in CLI mode
```

On macOS or Linux, prefix the command with `PYTHONPATH=src`, for example `PYTHONPATH=src python -m kuid2hash.cli`.

The `kuid2hash` command is created by installing the package (for example, with `python -m pip install -e ".[gui]"`); it is not available from a fresh source checkout. The GUI requires the optional PyQt6 dependency, which is included in the `gui` extra above.

CLI examples:

```
$ kuid2hash "kuid 68787 1097"
kuid:  <kuid:68787:1097>
hex:   B3 0C 01 00 49 04 00 00
hash:  hash-F3

$ kuid2hash "B3 0C 01 00 49 04 00 00"
kuid:  <kuid:68787:1097>
hex:   B3 0C 01 00 49 04 00 00
hash:  hash-F3
```

A single kuid may be passed quoted (`"kuid 68787 1097"`) or as separate tokens (`kuid2 328583 1373 2`). Hex kuids (4 bytes for `uid -1`, 8 bytes otherwise, separated by space/dash/colon/comma) are detected automatically.

## Building from source

Requires Python 3.10+.

```
python -m venv .venv
.venv\Scripts\pip install -e ".[gui,test]"     # Windows (use bin/activate on unix)
pytest                                         # run the tests
```

## Packaging

`build.py` builds distributable packages for the host OS:

| Platform | Artifact | Requirement |
|----------|----------|-------------|
| Windows  | `dist/Kuid2Hash.exe` (GUI) and `dist/Kuid2HashCli.exe` (CLI), both one-file | `pip install ".[gui,build]"` |
| macOS    | `dist/Kuid2Hash-<ver>-macos.dmg` | `pip install ".[gui,build]"` |
| Linux    | `dist/kuid2hash_<ver>_amd64.deb` and `.pkg.tar.zst` | `gem install fpm` |

```
python build.py                 # build everything this host supports
python build.py --only exe      # build a single artifact
```

PyInstaller cannot cross-compile, so each artifact must be built on its target OS. The GitHub Actions workflow in `.github/workflows/release.yml` builds all four packages (Windows exes, macOS dmg, Linux deb and zst) automatically on every `v*` tag and attaches them to the release.

On Windows the GUI and CLI ship as separate executables: a windowed exe cannot write to the console when invoked from a terminal with arguments, so `Kuid2Hash.exe` is the GUI and `Kuid2HashCli.exe` is the command line tool.

## System requirements

- Windows 10 or newer, macOS 12+ (Apple Silicon/Intel), or any recent Linux with Python 3.10+
- The GUI packages bundle PyQt6 (Qt 6); the deb/zst packages use the system Python and pull in its PyQt6 binding (`python3-pyqt6` on Debian/Ubuntu, `python-pyqt6` on Arch)

## Related Trainz tools

- [CDP Explorer](https://github.com/SilverGreen93/CDPExplorer)
- [TZ Archiver](https://github.com/SilverGreen93/TZarchiver)
- [Kuid Lister](https://github.com/SilverGreen93/KuidLister)
