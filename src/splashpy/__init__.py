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

"""Splash Sync Python Core: build Splash connectors for any Python application."""

from __future__ import annotations

from splashpy.client import SoapResponse, SplashClient
from splashpy.config import ConfigError, EnvConfig, JsonConfig, SplashConfig, StaticConfig
from splashpy.core import ClientInfo, Logger, RequestContext
from splashpy.extensions import Extension
from splashpy.version import __version__

__all__ = [
    "ClientInfo",
    "ConfigError",
    "EnvConfig",
    "Extension",
    "JsonConfig",
    "Logger",
    "RequestContext",
    "SoapResponse",
    "SplashClient",
    "SplashConfig",
    "StaticConfig",
    "__version__",
]
