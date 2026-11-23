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

"""WSGI gateway and command line, including a real HTTP round trip."""

from __future__ import annotations

import io
import threading
from collections.abc import Iterator
from typing import Any
from wsgiref.simple_server import WSGIServer, make_server

import pytest

from splashpy import SplashClient, SplashConfig, cli
from splashpy.adapters import SplashWsgiApp, make_app
from splashpy.adapters.wsgi import MAX_BODY
from splashpy.config import ConfigError
from splashpy.faker import FAKER_WS_ID
from splashpy.protocol import soap


def run_wsgi(
    app: Any, method: str = "POST", body: bytes = b"", path: str = "/splash", **extra: Any
) -> tuple[str, bytes]:
    """Run a WSGI request and return status and body."""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "SCRIPT_NAME": "",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        "wsgi.url_scheme": "http",
        "HTTP_HOST": "python.test",
        **extra,
    }
    captured: dict[str, str] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status

    content = b"".join(app(environ, start_response))
    return captured["status"], content


def test_wsgi_post(client: SplashClient) -> None:
    """POST requests are served."""
    status, body = run_wsgi(make_app(client), body=soap.build_request("Ping", ("x", ""), "urn:x"))
    assert status == "200 OK"
    assert soap.parse_response(body)


def test_wsgi_get_and_methods(client: SplashClient) -> None:
    """GET shows a name only; other methods are refused."""
    app = SplashWsgiApp(client, path="/splash")
    assert run_wsgi(app, "GET")[0] == "200 OK"
    assert run_wsgi(app, "PUT")[0] == "405 Method Not Allowed"
    assert run_wsgi(app, "POST", path="/other")[0] == "404 Not Found"
    assert run_wsgi(app, "POST", CONTENT_LENGTH=str(MAX_BODY + 1))[0] == "413 Payload Too Large"


def test_wsgi_fault_status(client: SplashClient) -> None:
    """Faults use the SOAP 1.1 HTTP status."""
    assert run_wsgi(make_app(client), body=b"garbage", CONTENT_LENGTH="x")[0].startswith("500")


def test_wsgi_factory(config: SplashConfig) -> None:
    """A factory builds one client per request (multi-tenant hosts)."""
    built: list[str] = []

    def factory(environ: Any) -> SplashClient:
        built.append(environ["HTTP_HOST"])
        return SplashClient(config)

    app = SplashWsgiApp(factory=factory)
    assert run_wsgi(app, body=soap.build_request("Ping", ("x", ""), "urn:x"))[0] == "200 OK"
    assert built == ["python.test"]
    with pytest.raises(ValueError, match="either"):
        SplashWsgiApp()


@pytest.fixture
def http_server(config: SplashConfig) -> Iterator[str]:
    """Serve a client on a real local HTTP server."""
    server: WSGIServer = make_server("127.0.0.1", 0, make_app(SplashClient(config)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()
    server.server_close()


def test_real_http_roundtrip(config: SplashConfig, http_server: str) -> None:
    """A client pings and connects another client through real HTTP (urllib transport)."""
    caller = SplashClient(SplashConfig(ws_id=config.ws_id, ws_key=config.ws_key, ws_host=http_server))
    assert caller.ping() is True
    assert caller.connect() is True


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    """``splashpy version`` prints the version."""
    assert cli.main(["version"]) == 0
    assert capsys.readouterr().out.strip()


def test_cli_config_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without configuration, only the faker falls back on development credentials."""
    for key in ("SPLASH_WS_ID", "SPLASH_WS_KEY"):
        monkeypatch.delenv(key, raising=False)
    assert cli.load_config(None, faker=True).ws_id == FAKER_WS_ID
    with pytest.raises(ConfigError):
        cli.load_config(None, faker=False)


def test_cli_serve_without_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Serving without configuration (and without faker) fails cleanly."""
    for key in ("SPLASH_WS_ID", "SPLASH_WS_KEY"):
        monkeypatch.delenv(key, raising=False)
    assert cli.main(["serve"]) == 2


def test_cli_serve(monkeypatch: pytest.MonkeyPatch) -> None:
    """``splashpy serve --faker`` builds a faker client and serves it."""
    served: dict[str, Any] = {}

    class FakeServer:
        def __enter__(self) -> FakeServer:
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

    def fake_make_server(host: str, port: int, app: SplashWsgiApp, *args: Any) -> FakeServer:
        served.update(host=host, port=port, app=app)
        return FakeServer()

    monkeypatch.setattr(cli, "make_server", fake_make_server)
    assert cli.main(["serve", "--faker", "--port", "8123", "--path", "/splash"]) == 0
    assert served["port"] == 8123
    assert run_wsgi(served["app"], "GET")[0] == "200 OK"
