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

"""Serving Splash requests: behaviours checked by the Toolkit validator."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from splashpy import RequestContext, SplashClient
from splashpy.client import HTTP_FAULT
from splashpy.dictionary import SplAdminMethods, SplServices
from splashpy.protocol import MessageCodec, soap
from splashpy.server import TaskRunner
from tests.conftest import CallServer, decode_response


def admin_tasks(*names: str) -> dict[str, Any]:
    """Build an Admin request with tasks indexed as Php-Core sends them."""
    tasks = {f"array-{i}": {"id": i, "name": name, "desc": f"Test {name}"} for i, name in enumerate(names, 1)}
    return {"debug": 1, "verbose": 1, "tasks": tasks}


def test_ping(call_server: CallServer, codec: MessageCodec) -> None:
    """Ping is unsecured and always successful, whatever the id."""
    response = call_server(SplServices.PING, ws_id="anything", secured=False)
    assert decode_response(response, codec, secured=False) == {"result": "1"}


def test_connect(call_server: CallServer, codec: MessageCodec) -> None:
    """Connect returns an encrypted positive result, with server information and logs."""
    data = decode_response(call_server(SplServices.CONNECT, {"connect": True}), codec)
    assert data is not None
    assert data["result"] == "1"
    assert data["server"]["ServerType"] == "Python"
    assert data["server"]["ServerHost"] == "http://python.test"
    assert "Connection Requested" in data["log"]["msg"]["string-0"]


def test_connect_rejects_wrong_ids(call_server: CallServer, codec: MessageCodec) -> None:
    """Wrong or empty ids give an EMPTY response (Toolkit A02)."""
    for ws_id in ("", "123456789"):
        response = call_server(SplServices.CONNECT, {"connect": True}, ws_id=ws_id)
        assert decode_response(response, codec) is None


def test_connect_rejects_wrong_encryption(call_server: CallServer) -> None:
    """Data encrypted with another key gives an EMPTY response (Toolkit A02)."""
    other = MessageCodec("AnotherKey", "ThisIsSplashWsId")
    response = call_server(SplServices.CONNECT, raw=other.pack({"connect": True}))
    assert soap.parse_response(response.body) is None


def test_admin_tasks(call_server: CallServer, codec: MessageCodec) -> None:
    """Admin tasks answer like Php-Core; empty lists are failures."""
    payload = admin_tasks(
        SplAdminMethods.INFOS, SplAdminMethods.SELF_TEST, SplAdminMethods.OBJECTS, SplAdminMethods.WIDGETS, "unknown"
    )
    data = decode_response(call_server(SplServices.ADMIN, payload), codec)
    assert data is not None
    tasks = data["tasks"]
    assert tasks["array-1"]["result"] == "1"
    assert tasks["array-1"]["data"]["shortdesc"].startswith("Splash Python Faker")
    assert tasks["array-1"]["id"] == "1"
    assert tasks["array-2"]["result"] == "1"
    assert tasks["array-3"]["result"] == "0"
    assert tasks["array-4"]["result"] == "0"
    assert tasks["array-5"]["result"] == "0"
    assert data["tasksinfos"]["Performed"] == "5"
    assert data["tasksinfos"]["Ok"] == "2"
    assert data["result"] == "0"
    assert "Admin - Requested task not found => unknown" in data["log"]["err"].values()
    assert data["log"]["deb"]


def test_admin_wrong_id(call_server: CallServer, codec: MessageCodec) -> None:
    """Admin with a wrong id gives an empty response."""
    assert decode_response(call_server(SplServices.ADMIN, admin_tasks("infos"), ws_id="x"), codec) is None


def test_admin_unreadable_data(call_server: CallServer) -> None:
    """Admin with unreadable data gives an empty response."""
    assert soap.parse_response(call_server(SplServices.ADMIN, raw="garbage").body) is None


def test_no_tasks(call_server: CallServer, codec: MessageCodec) -> None:
    """A request without tasks fails, with an error log."""
    data = decode_response(call_server(SplServices.ADMIN, {"debug": 0}), codec)
    assert data is not None
    assert data["result"] == "0"
    assert "task list is empty" in data["log"]["err"]["string-0"]


def test_invalid_task(call_server: CallServer, codec: MessageCodec) -> None:
    """A task that is not an array fails."""
    data = decode_response(call_server(SplServices.ADMIN, {"tasks": {"array-1": "x"}}), codec)
    assert data is not None
    assert data["result"] == "0"


def test_service_without_router(call_server: CallServer, codec: MessageCodec) -> None:
    """Services without router (until milestone 2) fail cleanly."""
    data = decode_response(call_server(SplServices.OBJECTS, admin_tasks("Objects")), codec)
    assert data is not None
    assert data["result"] == "0"
    assert "router doesn't exist" in data["log"]["err"]["string-0"]


def test_router_exception_is_reported(config: Any, codec: MessageCodec) -> None:
    """An exception in a router fails the task, never the request."""

    class Broken:
        def execute(self, task: Mapping[str, Any], ctx: RequestContext) -> dict[str, Any]:
            raise RuntimeError("router failure")

    outputs: dict[str, Any] = {}
    ctx = RequestContext(config=config)
    result = TaskRunner({"Admin": Broken()}).run("Admin", admin_tasks("infos"), outputs, ctx)
    assert result is False
    assert outputs["tasks"]["array-1"]["result"] is False
    assert ctx.logger.entries("err") == ["RuntimeError: router failure"]


def test_invalid_soap_request(client: SplashClient) -> None:
    """Invalid SOAP requests give a client fault."""
    response = client.handle_request(b"not xml")
    assert response.status == HTTP_FAULT
    assert b"SOAP-ENV:Client" in response.body


def test_unknown_service(client: SplashClient) -> None:
    """Unknown services give a client fault."""
    response = client.handle_request(soap.build_request("Unknown", ("a", "b"), "urn:x"))
    assert response.status == HTTP_FAULT


def test_unexpected_error_gives_server_fault(client: SplashClient, monkeypatch: Any) -> None:
    """Unexpected errors give a server fault, as Php-Core fatal handler."""

    def boom(*args: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(client._handler, "handle", boom)
    response = client.handle_request(soap.build_request("Admin", ("a", "b"), "urn:x"))
    assert response.status == HTTP_FAULT
    assert b"SOAP-ENV:Server" in response.body


def test_handle_returns_bytes(client: SplashClient, codec: MessageCodec) -> None:
    """``handle()`` is the pure bytes in / bytes out entry point."""
    body = client.handle(soap.build_request("Ping", ("id", ""), "urn:x"))
    assert codec.unpack(soap.parse_response(body) or "", secured=False) == {"result": "1"}
