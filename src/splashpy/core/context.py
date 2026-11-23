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

"""Per-request context: everything a request needs, nothing shared with other requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from splashpy.config import SplashConfig
from splashpy.core.logger import Logger


@dataclass
class RequestContext:
    """State of one request (incoming call from Splash, or outgoing call to Splash).

    A new context is created for every request, so a client can safely serve
    several requests at the same time from several threads.
    """

    config: SplashConfig
    """Configuration of the client serving the request."""

    logger: Logger = field(default_factory=Logger)
    """Messages returned to the Splash server with the response."""

    server_mode: bool = True
    """True while serving a request from Splash: commits are then not allowed."""

    debug: bool = False
    """Debug mode requested by the Splash server."""

    remote_server: dict[str, Any] = field(default_factory=dict)
    """Server information sent by the remote side."""

    server_host: str | None = None
    """Host of the incoming HTTP request (used when not configured)."""

    server_path: str | None = None
    """Path of the incoming HTTP request (used when not configured)."""

    user_agent: str | None = None
    """User agent of the incoming HTTP request."""


def php_truthy(value: Any) -> bool:
    """Mirror of PHP truthiness for decoded values (``"0"`` and ``""`` are false)."""
    if isinstance(value, str):
        return value not in ("", "0")

    return bool(value)
