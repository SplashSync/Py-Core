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

"""Configuration, logger, context and information."""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any

import pytest

from splashpy import ClientInfo, ConfigError, EnvConfig, JsonConfig, Logger, SplashConfig, StaticConfig
from splashpy.config import resolve
from splashpy.core import RequestContext, php_truthy, server_info
from splashpy.dictionary import SplDefinition

# ====================================================================#
# Configuration
# ====================================================================#


@pytest.mark.parametrize(
    "settings",
    [
        {"ws_id": "", "ws_key": "k"},
        {"ws_id": "i", "ws_key": ""},
        {"ws_id": "i", "ws_key": "k", "ws_host": ""},
        {"ws_id": "i", "ws_key": "k", "ws_timeout": 0},
        {"ws_id": "i", "ws_key": "k", "http_user": "user"},
    ],
)
def test_invalid_config(settings: dict[str, Any]) -> None:
    """Incomplete configurations are refused."""
    with pytest.raises(ConfigError):
        SplashConfig(**settings).validate()


def test_secrets_are_never_printed() -> None:
    """Keys and passwords do not appear in the representation."""
    config = SplashConfig(ws_id="id", ws_key="SECRET-KEY", http_user="u", http_password="SECRET-PWD")
    assert "SECRET" not in repr(config)


def test_static_config(config: SplashConfig) -> None:
    """A static provider returns its configuration."""
    assert StaticConfig(config).load() is config
    assert resolve(StaticConfig(config)) is config
    assert resolve(config) is config


def test_env_config() -> None:
    """Environment variables are read with their prefix."""
    environ = {
        "SPLASH_WS_ID": "id",
        "SPLASH_WS_KEY": "key",
        "SPLASH_WS_TIMEOUT": "12",
        "SPLASH_EXTENSIONS": "faker, other ,",
        "OTHER": "ignored",
    }
    config = EnvConfig(environ=environ).load()
    assert (config.ws_id, config.ws_key, config.ws_timeout) == ("id", "key", 12)
    assert config.extensions == ("faker", "other")


def test_env_config_missing() -> None:
    """Missing environment variables are reported."""
    with pytest.raises(ConfigError):
        EnvConfig(environ={}).load()


def test_json_config(tmp_path: Path) -> None:
    """JSON files are read."""
    path = tmp_path / "splash.json"
    path.write_text(json.dumps({"ws_id": "id", "ws_key": "key", "extensions": ["faker"]}))
    config = JsonConfig(path).load()
    assert (config.ws_id, config.extensions) == ("id", ("faker",))


@pytest.mark.parametrize(
    "content",
    ["not json", "[1, 2]", json.dumps({"ws_id": "i", "ws_key": "k", "unknown": 1}), json.dumps({"ws_key": "k"})],
)
def test_json_config_errors(tmp_path: Path, content: str) -> None:
    """Unreadable, unknown or incomplete settings are reported."""
    path = tmp_path / "splash.json"
    path.write_text(content)
    with pytest.raises(ConfigError):
        JsonConfig(path).load()


def test_json_config_missing_file(tmp_path: Path) -> None:
    """A missing file is reported."""
    with pytest.raises(ConfigError):
        JsonConfig(tmp_path / "missing.json").load()


def test_invalid_timeout() -> None:
    """Timeouts must be integers."""
    with pytest.raises(ConfigError):
        EnvConfig(environ={"SPLASH_WS_ID": "i", "SPLASH_WS_KEY": "k", "SPLASH_WS_TIMEOUT": "x"}).load()


# ====================================================================#
# Logger
# ====================================================================#


def test_logger_levels() -> None:
    """Entries are stored by kind; debug only in verbose mode."""
    logger = Logger()
    assert logger.error("e") is False
    assert logger.warning("w") is True
    assert logger.info("m") is True
    assert logger.debug("hidden") is True
    assert logger.export() == {"err": ["e"], "war": ["w"], "msg": ["m"], "deb": []}
    assert logger.has_errors
    logger.verbose = True
    logger.debug("d")
    assert logger.entries("deb") == ["d"]


def test_logger_exception() -> None:
    """Exceptions are reported with their traceback in debug."""
    logger = Logger(verbose=True)
    error: RuntimeError | None = None
    try:
        raise RuntimeError("boom")
    except RuntimeError as raised:
        error = raised
    assert error is not None
    assert logger.exception(error) is False
    assert logger.entries("err") == ["RuntimeError: boom"]
    assert "Traceback" in logger.entries("deb")[0]


def test_logger_merge() -> None:
    """Raw logs received from Splash (decoded dicts or lists) are merged."""
    logger = Logger()
    logger.merge({"msg": {"string-0": "a", "string-1": "b"}, "err": ["c"], "war": "", "deb": None})
    logger.merge("not a log")
    assert logger.export() == {"err": ["c"], "war": [], "msg": ["a", "b"], "deb": []}


def test_logger_flush(caplog: pytest.LogCaptureFixture) -> None:
    """Flushing writes to a Python logger and clears."""
    logger = Logger()
    logger.error("an error")
    with caplog.at_level(logging.INFO):
        logger.flush(logging.getLogger("test"))
    assert "an error" in caplog.text
    assert not logger.has_errors


# ====================================================================#
# Context & Information
# ====================================================================#


@pytest.mark.parametrize(("value", "expected"), [("0", False), ("", False), ("1", True), (None, False), (1, True)])
def test_php_truthy(value: Any, expected: bool) -> None:
    """Decoded values follow PHP truthiness."""
    assert php_truthy(value) is expected


def test_server_info(config: SplashConfig) -> None:
    """Server information uses the request when not configured."""
    info = server_info(RequestContext(config=config, server_host="http://host", server_path="/splash"))
    assert info["ServerType"] == SplDefinition.SERVER_TYPE
    assert info["ProtocolVersion"] == SplDefinition.PROTOCOL
    assert (info["ServerHost"], info["ServerPath"]) == ("http://host", "/splash")


def test_client_info_default_icons() -> None:
    """Default icons are the packaged Python images, base64 encoded."""
    data = ClientInfo().to_dict()
    assert base64.b64decode(data["logoraw"]).startswith(b"\x89PNG")
    assert data["icoraw"]
    assert data["moduleversion"] == SplDefinition.VERSION
