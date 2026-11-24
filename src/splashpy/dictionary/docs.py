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

"""Documentation: where splashpy documentation pages are found (repository or installed package)."""

from __future__ import annotations

from typing import Final


class SplDocs:
    """Documentation files and locations."""

    INDEX: Final = "llms.txt"
    """Documentation index for humans & agents (llmstxt.org format)."""

    DIRECTORY: Final = "docs"
    """Pages directory: at the repository root, and inside the package once built."""

    EXTENSION: Final = ".md"
    """Pages extension (Markdown)."""
