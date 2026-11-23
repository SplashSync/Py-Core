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

"""HTTP transport: an injectable interface and a standard library implementation."""

from __future__ import annotations

import base64
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Protocol
from urllib.parse import urlparse


class TransportError(Exception):
    """Raised when an HTTP request cannot be performed."""


class Transport(Protocol):
    """Send one HTTP POST request and return the response body."""

    def post(self, url: str, body: bytes, headers: Mapping[str, str], timeout: float) -> bytes:
        """Post a request and return the response body (also for HTTP errors carrying a body).

        :raises TransportError: when no response could be obtained.
        """
        ...


class UrllibTransport:
    """Transport based on ``urllib`` (no dependency)."""

    def __init__(self, user: str | None = None, password: str | None = None) -> None:
        """Optionally use HTTP basic authentication."""
        self._auth: str | None = None
        if user and password:
            token = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
            self._auth = f"Basic {token}"

    def post(self, url: str, body: bytes, headers: Mapping[str, str], timeout: float) -> bytes:
        """Post a request with ``urllib``; HTTP error bodies (e.g. SOAP faults) are returned."""
        if urlparse(url).scheme not in ("http", "https"):
            raise TransportError(f"Unsupported URL scheme: {url}")
        request = urllib.request.Request(url, data=body, method="POST")
        for name, value in headers.items():
            request.add_header(name, value)
        if self._auth:
            request.add_header("Authorization", self._auth)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
                return bytes(response.read())
        except urllib.error.HTTPError as error:
            content = error.read()
            if content:
                return bytes(content)
            raise TransportError(f"HTTP error {error.code} from {url}") from error
        except (urllib.error.URLError, OSError) as error:
            raise TransportError(f"Unable to reach {url}: {error}") from error
