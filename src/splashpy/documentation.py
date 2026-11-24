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

"""Documentation reader: the pages of the installed splashpy version, for humans & coding agents.

Built packages ship the pages and the index inside splashpy/docs/; editable installs read them
from the repository (index at the root, pages in docs/). Planning notes are never shipped.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, Union

from splashpy.dictionary import SplDocs

if TYPE_CHECKING:
    from importlib.abc import Traversable

    Location = Union[Path, Traversable]


class DocsError(LookupError):
    """Unknown documentation page, or documentation not available."""


@dataclass(frozen=True)
class DocsSource:
    """Where the documentation index and pages are read from."""

    index: Location
    """Index file (``llms.txt``)."""

    pages: Location
    """Pages directory."""

    def names(self) -> list[str]:
        """Get the names of the available pages, sorted."""
        if not self.pages.is_dir():
            return []
        names = (entry.name for entry in self.pages.iterdir() if entry.is_file())
        return sorted(name[: -len(SplDocs.EXTENSION)] for name in names if name.endswith(SplDocs.EXTENSION))

    def read_index(self) -> str:
        """Read the documentation index.

        :raises DocsError: when the documentation is not available.
        """
        if not self.index.is_file():
            raise DocsError("splashpy documentation is not available in this installation.")
        return self.index.read_text(encoding="utf-8")

    def read_page(self, name: str) -> str:
        """Read one page, by name (with or without extension).

        Only listed pages can be read: a name never builds a path by itself.

        :raises DocsError: when the page is unknown.
        """
        names = self.names()
        page = name[: -len(SplDocs.EXTENSION)] if name.endswith(SplDocs.EXTENSION) else name
        if page not in names:
            raise DocsError(f"Unknown documentation page '{name}', available: {', '.join(names) or '-'}.")
        return self.pages.joinpath(page + SplDocs.EXTENSION).read_text(encoding="utf-8")


def packaged_source() -> DocsSource:
    """Get the documentation shipped inside the built package."""
    pages = resources.files("splashpy").joinpath(SplDocs.DIRECTORY)
    return DocsSource(pages.joinpath(SplDocs.INDEX), pages)


def repository_source(root: Path | None = None) -> DocsSource:
    """Get the documentation of a repository checkout (editable installs)."""
    root = root or Path(__file__).resolve().parents[2]
    return DocsSource(root / SplDocs.INDEX, root / SplDocs.DIRECTORY)


def docs_source() -> DocsSource:
    """Get the documentation of this installation: packaged first, repository otherwise."""
    packaged = packaged_source()
    return packaged if packaged.index.is_file() else repository_source()
