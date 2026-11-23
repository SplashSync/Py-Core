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

"""Client information (shown in Splash) and technical server information."""

from __future__ import annotations

import base64
import platform
import socket
from dataclasses import asdict, dataclass, field
from importlib import resources
from typing import Any

from splashpy.core.context import RequestContext
from splashpy.dictionary import SplDefinition


def asset(name: str) -> str:
    """Read a packaged asset, base64 encoded (as Php-Core ``readFileContents()``)."""
    raw = resources.files("splashpy").joinpath("assets").joinpath(name).read_bytes()

    return base64.b64encode(raw).decode("ascii")


@dataclass
class ClientInfo:
    """General information about this client, as returned by the Admin ``infos`` task."""

    shortdesc: str = f"{SplDefinition.NAME} {SplDefinition.VERSION}"
    """Short description of the connector."""

    longdesc: str = SplDefinition.DESC
    """Long description of the connector."""

    company: str | None = None
    """Company name."""

    address: str | None = None
    """Company address."""

    zip: str | None = None
    """Company zip code."""

    town: str | None = None
    """Company town."""

    country: str | None = None
    """Company country."""

    www: str | None = None
    """Company website."""

    email: str | None = None
    """Company email."""

    phone: str | None = None
    """Company phone."""

    icoraw: str | None = None
    """Icon, base64 encoded (default: Python icon)."""

    logourl: str | None = None
    """Logo URL."""

    logoraw: str | None = None
    """Logo, base64 encoded (default: Python logo)."""

    scopes: list[str] = field(default_factory=list)
    """Codes of the scopes implemented by this client."""

    servertype: str = SplDefinition.NAME
    """Server type, e.g. the host application name."""

    serverurl: str | None = None
    """Server URL of the host application."""

    moduleauthor: str = SplDefinition.AUTHOR
    """Module author."""

    moduleversion: str = SplDefinition.VERSION
    """Module version."""

    def to_dict(self) -> dict[str, Any]:
        """Export information, with default icons when none are given."""
        data = asdict(self)
        data["icoraw"] = self.icoraw or asset("python.ico")
        data["logoraw"] = self.logoraw or asset("python.png")

        return data


def server_info(ctx: RequestContext) -> dict[str, Any]:
    """Technical information about this server (mirror of Php-Core ``ServerInfos::getInfos()``)."""
    try:
        address = socket.gethostbyname(socket.gethostname())
    except OSError:
        address = ""

    return {
        "ServerType": SplDefinition.SERVER_TYPE,
        "ServerVersion": platform.python_version(),
        "ProtocolVersion": SplDefinition.PROTOCOL,
        "Self": "",
        "ServerAddress": address,
        "ServerRoot": "",
        "UserAgent": ctx.user_agent or "",
        "WsMethod": SplDefinition.WS_METHOD,
        "ServerHost": ctx.config.server_host or ctx.server_host or "",
        "ServerIP": address,
        "ServerPath": ctx.config.server_path or ctx.server_path or "",
    }
