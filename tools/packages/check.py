#
#  This file is part of SplashSync Project.
#
#  Copyright (C) Splash Sync  <www.splashsync.com>
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  For the full copyright and license information, please view the LICENSE
#  file that was distributed with this source code.
#

"""Check built packages before publishing: documentation shipped, planning notes never.

Usage: ``python tools/packages/check.py dist/`` (standard library only, runs in any Python 3.9+).
"""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

REQUIRED = ("splashpy/docs/llms.txt", "splashpy/docs/getting-started.md", "splashpy/contracts/data/index.json")
"""Files every wheel must contain."""

FORBIDDEN = "docs/plan/"
"""Planning notes: never published."""


def wheel_names(path: Path) -> list[str]:
    """List the files of a wheel."""
    with zipfile.ZipFile(path) as archive:
        return archive.namelist()


def sdist_names(path: Path) -> list[str]:
    """List the files of a source distribution, without the top directory."""
    with tarfile.open(path) as archive:
        return [name.split("/", 1)[-1] for name in archive.getnames()]


def check(directory: Path) -> list[str]:
    """Check every package of a directory, return the errors."""
    errors: list[str] = []
    wheels = sorted(directory.glob("*.whl"))
    if not wheels:
        errors.append(f"No wheel found in {directory}.")
    for wheel in wheels:
        names = wheel_names(wheel)
        errors += [f"{wheel.name}: missing {name}" for name in REQUIRED if name not in names]
        errors += [f"{wheel.name}: forbidden {name}" for name in names if FORBIDDEN in name]
    for sdist in sorted(directory.glob("*.tar.gz")):
        errors += [f"{sdist.name}: forbidden {name}" for name in sdist_names(sdist) if FORBIDDEN in name]
    return errors


def main(argv: list[str]) -> int:
    """Check the packages of the given directory (default: dist)."""
    errors = check(Path(argv[1] if len(argv) > 1 else "dist"))
    for error in errors:
        print(f"ERROR: {error}")
    print("Packages OK." if not errors else f"{len(errors)} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
