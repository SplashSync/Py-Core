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

"""Client configuration: immutable settings and the providers able to build them."""

from __future__ import annotations

from splashpy.config.config import ConfigError, SplashConfig
from splashpy.config.providers import ConfigProvider, EnvConfig, JsonConfig, StaticConfig, resolve

__all__ = [
    "ConfigError",
    "ConfigProvider",
    "EnvConfig",
    "JsonConfig",
    "SplashConfig",
    "StaticConfig",
    "resolve",
]
