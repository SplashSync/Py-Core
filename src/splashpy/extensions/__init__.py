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

"""Extensions: what an add-on can contribute to a client.

Milestone 1 only defines the base class. The per-client registry, entry points
discovery (allowlist only) and the extension field groups come in milestone 2.
"""

from __future__ import annotations

from typing import ClassVar

from splashpy.core.info import ClientInfo


class Extension:
    """Base class of every extension."""

    name: ClassVar[str] = ""
    """Unique extension name, used in configuration allowlists."""

    priority: ClassVar[int] = 0
    """Execution priority: the lower, the earlier."""

    def client_info(self, info: ClientInfo) -> ClientInfo:
        """Complete or override client information. Default: unchanged."""
        return info


__all__ = ["Extension"]
