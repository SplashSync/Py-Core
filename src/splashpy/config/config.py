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

"""Immutable configuration of one Splash client."""

from __future__ import annotations

from dataclasses import dataclass, field

from splashpy.dictionary import SplDefinition


class ConfigError(ValueError):
    """Raised when a configuration is incomplete or invalid."""


@dataclass(frozen=True)
class SplashConfig:
    """Settings of one Splash client (one per database / tenant if needed).

    Instances are immutable: build a new one to change a setting.
    """

    ws_id: str
    """Webservice identifier of this node, given by Splash."""

    ws_key: str = field(repr=False)
    """Shared encryption key, given by Splash. Never printed."""

    ws_host: str = SplDefinition.HOST
    """Splash server endpoint, used for outgoing calls (commits, self test...)."""

    ws_timeout: int = SplDefinition.TIMEOUT
    """Timeout of outgoing calls, in seconds."""

    lang: str = SplDefinition.LANG
    """Default language (ISO code, e.g. ``en_US``)."""

    http_user: str | None = None
    """HTTP basic auth user for outgoing calls, if the server requires it."""

    http_password: str | None = field(default=None, repr=False)
    """HTTP basic auth password for outgoing calls. Never printed."""

    server_host: str | None = None
    """Public host of this connector, reported to Splash (detected from requests when empty)."""

    server_path: str | None = None
    """Public path of this connector endpoint (detected from requests when empty)."""

    extensions: tuple[str, ...] = ()
    """Names of the installed (entry point) extensions to enable. Nothing is enabled implicitly."""

    def validate(self) -> SplashConfig:
        """Check the configuration is usable.

        :raises ConfigError: on missing or invalid settings.
        """
        if not self.ws_id:
            raise ConfigError("Webservice identifier (ws_id) is missing.")
        if not self.ws_key:
            raise ConfigError("Encryption key (ws_key) is missing.")
        if not self.ws_host:
            raise ConfigError("Splash server host (ws_host) is missing.")
        if self.ws_timeout <= 0:
            raise ConfigError("Webservice timeout must be above 0.")
        if bool(self.http_user) != bool(self.http_password):
            raise ConfigError("HTTP auth requires both user and password.")

        return self
