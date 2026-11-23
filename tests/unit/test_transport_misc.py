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

"""HTTP transport, extensions base and small helpers."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from splashpy import ClientInfo, Extension, RequestContext, SplashConfig
from splashpy.protocol import MessageCodec
from splashpy.server import ServiceHandler, TaskRunner
from splashpy.server.routers import task_params
from splashpy.transport import TransportError, UrllibTransport


class Handler(BaseHTTPRequestHandler):
    """Answer according to the requested path, echoing the Authorization header."""

    def do_POST(self) -> None:
        """Serve one request."""
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.path == "/fault":
            self._send(500, b"<fault/>")
        elif self.path == "/empty-error":
            self._send(503, b"")
        else:
            self._send(200, (self.headers.get("Authorization") or "none").encode())

    def _send(self, status: int, body: bytes) -> None:
        """Send a response."""
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        """Stay quiet."""


@pytest.fixture
def server_url() -> Iterator[str]:
    """Run a local HTTP server."""
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_post_without_auth(server_url: str) -> None:
    """A plain request reaches the server."""
    assert UrllibTransport().post(f"{server_url}/ok", b"x", {"X-Test": "1"}, 5) == b"none"


def test_post_with_basic_auth(server_url: str) -> None:
    """Basic auth credentials are sent."""
    assert UrllibTransport("user", "pwd").post(f"{server_url}/ok", b"x", {}, 5) == b"Basic dXNlcjpwd2Q="


def test_http_error_body_is_returned(server_url: str) -> None:
    """HTTP errors carrying a body (SOAP faults) are returned."""
    assert UrllibTransport().post(f"{server_url}/fault", b"x", {}, 5) == b"<fault/>"


def test_http_error_without_body(server_url: str) -> None:
    """HTTP errors without body are transport errors."""
    with pytest.raises(TransportError, match="503"):
        UrllibTransport().post(f"{server_url}/empty-error", b"x", {}, 5)


def test_unreachable_and_bad_scheme() -> None:
    """Unreachable hosts and non HTTP schemes are refused."""
    with pytest.raises(TransportError):
        UrllibTransport().post("http://127.0.0.1:9/", b"x", {}, 1)
    with pytest.raises(TransportError, match="scheme"):
        UrllibTransport().post("file:///etc/passwd", b"x", {}, 1)


def test_extension_defaults() -> None:
    """The base extension changes nothing."""
    info = ClientInfo()
    assert Extension().client_info(info) is info


def test_task_params() -> None:
    """Task parameters default to an empty mapping."""
    assert task_params({"params": {"type": "X"}}) == {"type": "X"}
    assert task_params({"params": "broken"}) == {}
    assert task_params({}) == {}


def test_runner_exception_fails_request(config: SplashConfig) -> None:
    """An exception escaping the runner fails the request but still answers."""

    class BrokenRunner(TaskRunner):
        def run(self, *args: Any) -> bool:
            raise RuntimeError("runner failure")

    codec = MessageCodec(config.ws_key, config.ws_id)
    handler = ServiceHandler(codec, BrokenRunner({}))
    ctx = RequestContext(config=config)
    response = handler.handle("Admin", config.ws_id, codec.pack({"tasks": {"a": {}}}), ctx)
    assert response is not None
    assert codec.unpack(response)["result"] == "0"
    assert ctx.logger.entries("err") == ["RuntimeError: runner failure"]
