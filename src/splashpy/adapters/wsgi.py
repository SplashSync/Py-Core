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

"""Generic WSGI gateway, standard library only.

Any WSGI server (gunicorn, uWSGI, ``wsgiref``...) or framework able to mount a
WSGI application can serve a Splash client with :class:`SplashWsgiApp`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Callable, Final

from splashpy.client import SplashClient
from splashpy.dictionary import SplDefinition

if TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse, WSGIEnvironment

MAX_BODY: Final = 128 * 1024 * 1024
"""Maximum accepted request body, in bytes."""

_STATUS: Final = {200: "200 OK", 404: "404 Not Found", 405: "405 Method Not Allowed", 413: "413 Payload Too Large"}
"""HTTP status lines."""


class SplashWsgiApp:
    """WSGI application serving one Splash client, or one client per request."""

    def __init__(
        self,
        client: SplashClient | None = None,
        *,
        factory: Callable[[WSGIEnvironment], SplashClient] | None = None,
        path: str | None = None,
    ) -> None:
        """Serve a fixed client, or a client built per request by ``factory`` (multi-tenant).

        :param path: only serve this path (any path when None).
        """
        if (client is None) == (factory is None):
            raise ValueError("Give either a client or a factory.")
        self._client = client
        self._factory = factory
        self._path = path

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
        """Serve one HTTP request."""
        path = environ.get("SCRIPT_NAME", "") + environ.get("PATH_INFO", "")
        if self._path is not None and path.rstrip("/") != self._path.rstrip("/"):
            return self._reply(start_response, 404, b"Not Found", "text/plain")
        method = environ.get("REQUEST_METHOD", "GET")
        if method == "GET":
            return self._reply(start_response, 200, f"{SplDefinition.NAME}".encode(), "text/plain")
        if method != "POST":
            return self._reply(start_response, 405, b"Method Not Allowed", "text/plain")
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        if length > MAX_BODY:
            return self._reply(start_response, 413, b"Payload Too Large", "text/plain")
        body = environ["wsgi.input"].read(length) if length else b""
        client = self._client if self._client is not None else self._build(environ)
        response = client.handle_request(
            body,
            server_host=self._host(environ),
            server_path=path or "/",
            user_agent=environ.get("HTTP_USER_AGENT"),
        )

        return self._reply(start_response, response.status, response.body, response.content_type)

    # ====================================================================#
    # Private Methods
    # ====================================================================#

    def _build(self, environ: WSGIEnvironment) -> SplashClient:
        """Build the client of this request."""
        if self._factory is None:
            raise RuntimeError("No client factory configured.")

        return self._factory(environ)

    @staticmethod
    def _host(environ: WSGIEnvironment) -> str:
        """Public URL host of the request, with scheme."""
        scheme = environ.get("wsgi.url_scheme", "http")
        host = environ.get("HTTP_HOST") or environ.get("SERVER_NAME", "")

        return f"{scheme}://{host}"

    @staticmethod
    def _reply(start_response: StartResponse, status: int, body: bytes, content_type: str) -> list[bytes]:
        """Send a response."""
        headers: list[tuple[str, str]] = [("Content-Type", content_type), ("Content-Length", str(len(body)))]
        start_response(_STATUS.get(status, f"{status} Internal Server Error"), headers)

        return [body]


def make_app(client: SplashClient, path: str | None = None) -> SplashWsgiApp:
    """Build a WSGI application serving one client."""
    return SplashWsgiApp(client, path=path)
