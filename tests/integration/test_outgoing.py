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

"""Outgoing calls to Splash, through fake transports."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from splashpy import SplashClient, SplashConfig
from splashpy.dictionary import SplObjectMethods, SplOperations, SplServices
from splashpy.protocol import MessageCodec, soap
from splashpy.transport import TransportError
from tests.support import Memory


class FakeSplashServer:
    """Transport answering like the Splash server, recording requests."""

    def __init__(self, config: SplashConfig, result: bool = True, fault: bool = False, empty: bool = False) -> None:
        """Prepare the fake server answers."""
        self.codec = MessageCodec(config.ws_key, config.ws_id)
        self.result = result
        self.fault = fault
        self.empty = empty
        self.requests: list[dict[str, Any]] = []

    def post(self, url: str, body: bytes, headers: Mapping[str, str], timeout: float) -> bytes:
        """Decode the request and answer."""
        call = soap.parse_request(body)
        secured = call.service != SplServices.PING
        inputs = self.codec.unpack(call.params[1] or "", secured)
        self.requests.append({"url": url, "headers": dict(headers), "call": call, "inputs": inputs})
        if self.fault:
            return soap.build_fault(soap.FAULT_SERVER, "Server down")
        if self.empty:
            return soap.build_response(call.service, None)
        outputs = {"result": self.result, "log": {"msg": ["Hello from Splash"]}}
        return soap.build_response(call.service, self.codec.pack(outputs, secured))


class DownTransport:
    """Transport that never reaches the server."""

    def post(self, url: str, body: bytes, headers: Mapping[str, str], timeout: float) -> bytes:
        """Fail."""
        raise TransportError("unreachable")


def make_client(config: SplashConfig, transport: Any, **settings: Any) -> SplashClient:
    """Build a client on a transport, exposing a ThirdParty object."""

    class ThirdParty(Memory):
        pass

    if settings:
        config = SplashConfig(**{**config.__dict__, **settings})
    return SplashClient(config, objects=[ThirdParty()], transport=transport)


def test_ping(config: SplashConfig) -> None:
    """Ping is sent unsecured with server information."""
    server = FakeSplashServer(config)
    assert make_client(config, server).ping() is True
    request = server.requests[0]
    assert request["url"] == "http://splash.test/ws/soap"
    assert request["inputs"]["service"] == "Ping"
    assert "tasks" not in request["inputs"]
    assert request["headers"]["SOAPAction"] == '"http://splash.test/ws/soap#Ping"'


def test_connect(config: SplashConfig) -> None:
    """Connect is sent encrypted with an empty tasks list."""
    server = FakeSplashServer(config)
    assert make_client(config, server).connect() is True
    assert server.requests[0]["inputs"]["tasks"] == ""


def test_connect_negative(config: SplashConfig) -> None:
    """A negative answer is a failure."""
    assert make_client(config, FakeSplashServer(config, result=False)).connect() is False


def test_commit(config: SplashConfig) -> None:
    """Commits are sent as Objects / Commit tasks."""
    server = FakeSplashServer(config)
    client = make_client(config, server, ws_host="splash.test/ws/soap", server_host="http://me.test")
    assert client.commit("ThirdParty", [12, "13"], SplOperations.UPDATE, "admin", "Updated") is True
    request = server.requests[0]
    assert request["url"] == "https://splash.test/ws/soap"
    assert request["call"].uri == "http://me.test"
    task = request["inputs"]["tasks"]["array-1"]
    assert task["name"] == SplObjectMethods.COMMIT
    assert task["params"] == {
        "type": "ThirdParty",
        "id": {"string-0": "12", "string-1": "13"},
        "action": "update",
        "user": "admin",
        "comment": "Updated",
    }
    assert request["inputs"]["taskscount"] == "1"


def test_commit_single_id(config: SplashConfig) -> None:
    """A single id is sent as a list."""
    server = FakeSplashServer(config)
    make_client(config, server).commit("ThirdParty", 12, SplOperations.CREATE)
    assert server.requests[0]["inputs"]["tasks"]["array-1"]["params"]["id"] == {"string-0": "12"}


@pytest.mark.parametrize(
    "transport_factory",
    [
        lambda config: FakeSplashServer(config, fault=True),
        lambda config: FakeSplashServer(config, empty=True),
        lambda config: DownTransport(),
    ],
)
def test_failures(config: SplashConfig, transport_factory: Any, caplog: pytest.LogCaptureFixture) -> None:
    """Faults, empty responses and unreachable servers are failures, logged."""
    client = make_client(config, transport_factory(config))
    assert client.ping() is False
    assert client.connect() is False
    assert "Ping" in caplog.text


def test_call_returns_decoded_response(config: SplashConfig) -> None:
    """Generic calls return the decoded response and merge its logs."""
    client = make_client(config, FakeSplashServer(config))
    ctx = client.new_context(server_mode=False)
    response: dict[str, Any] | None = client.call(SplServices.ADMIN, {}, ctx=ctx)
    assert response is not None
    assert response["result"] == "1"
