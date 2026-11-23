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

"""Configuration providers: static, environment variables or JSON file."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final, Protocol, runtime_checkable

from splashpy.config.config import ConfigError, SplashConfig

# ====================================================================#
# Settings Keys
# ====================================================================#

KEYS: Final = (
    "ws_id",
    "ws_key",
    "ws_host",
    "ws_timeout",
    "lang",
    "http_user",
    "http_password",
    "server_host",
    "server_path",
    "extensions",
)
"""Accepted settings keys (lower case in JSON, upper case with prefix in environment)."""

ENV_PREFIX: Final = "SPLASH_"
"""Default prefix of environment variables."""


@runtime_checkable
class ConfigProvider(Protocol):
    """Anything able to build a :class:`SplashConfig`."""

    def load(self) -> SplashConfig:
        """Build the configuration."""
        ...


class StaticConfig:
    """Provider returning a configuration given in code."""

    def __init__(self, config: SplashConfig) -> None:
        """Store the configuration."""
        self._config = config

    def load(self) -> SplashConfig:
        """Return the stored configuration."""
        return self._config.validate()


class EnvConfig:
    """Provider reading ``SPLASH_WS_ID``, ``SPLASH_WS_KEY``... environment variables."""

    def __init__(self, prefix: str = ENV_PREFIX, environ: Mapping[str, str] | None = None) -> None:
        """Choose the variables prefix and source (``os.environ`` by default)."""
        self._prefix = prefix
        self._environ = environ

    def load(self) -> SplashConfig:
        """Build the configuration from environment variables."""
        environ = os.environ if self._environ is None else self._environ
        values = {key: environ[self._prefix + key.upper()] for key in KEYS if self._prefix + key.upper() in environ}

        return build(values)


class JsonConfig:
    """Provider reading a JSON file (keys as in :data:`KEYS`)."""

    def __init__(self, path: str | Path) -> None:
        """Store the file path."""
        self._path = Path(path)

    def load(self) -> SplashConfig:
        """Build the configuration from the JSON file."""
        try:
            values = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ConfigError(f"Unable to read configuration file {self._path}: {error}") from error
        if not isinstance(values, dict):
            raise ConfigError(f"Configuration file {self._path} must contain a JSON object.")

        return build(values)


def build(values: Mapping[str, Any]) -> SplashConfig:
    """Build and validate a configuration from raw values.

    :raises ConfigError: on unknown keys or invalid values.
    """
    unknown = sorted(set(values) - set(KEYS))
    if unknown:
        raise ConfigError(f"Unknown configuration keys: {', '.join(unknown)}.")
    settings: dict[str, Any] = dict(values)
    if "ws_timeout" in settings:
        try:
            settings["ws_timeout"] = int(settings["ws_timeout"])
        except (TypeError, ValueError) as error:
            raise ConfigError("Webservice timeout must be an integer.") from error
    if "extensions" in settings:
        extensions = settings["extensions"]
        if isinstance(extensions, str):
            extensions = [name.strip() for name in extensions.split(",")]
        settings["extensions"] = tuple(name for name in extensions if name)
    try:
        config = SplashConfig(**settings)
    except TypeError as error:
        raise ConfigError(f"Invalid configuration: {error}") from error

    return config.validate()


def resolve(config: SplashConfig | ConfigProvider) -> SplashConfig:
    """Get a validated configuration from a configuration or a provider."""
    if isinstance(config, SplashConfig):
        return config.validate()

    return config.load()
