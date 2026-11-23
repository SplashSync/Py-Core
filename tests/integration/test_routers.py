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

"""Objects, Widgets and Files services, through the real protocol."""

from __future__ import annotations

from typing import Any, Callable

import pytest

from splashpy import SplashClient, SplashConfig
from splashpy.dictionary import SplFilesMethods, SplObjectMethods, SplServices, SplWidgetsMethods
from splashpy.fields import Files
from splashpy.protocol import MessageCodec, soap
from tests.support import Memory, Recorder

Call = Callable[..., dict[str, Any]]
"""Run one task and return its decoded response."""


@pytest.fixture
def memory() -> Memory:
    """Build an in-memory object."""
    return Memory()


@pytest.fixture
def call(config: SplashConfig, memory: Memory, codec: MessageCodec) -> Call:
    """Run one task on a client exposing the memory object and test widgets."""
    client = SplashClient(config, objects=[memory], extensions=[Recorder()])

    def _call(service: str, name: str, params: Any = None) -> dict[str, Any]:
        task: dict[str, Any] = {"id": 1, "name": name, "desc": "test"}
        if params is not None:
            task["params"] = params
        payload = {"verbose": 1, "tasks": {"1": task}}
        body = soap.build_request(service, (config.ws_id, codec.pack(payload)), "urn:test")
        data = codec.unpack(soap.parse_response(client.handle(body)) or "")
        response: dict[str, Any] = data["tasks"]["array-1"]
        response["log"] = data["log"]
        return response

    return _call


def objects(call: Call, name: str, params: Any = None) -> dict[str, Any]:
    """Run an Objects task."""
    return call(SplServices.OBJECTS, name, params)


# ====================================================================#
# Objects
# ====================================================================#


def test_objects_admin_tasks(call: Call) -> None:
    """Objects, Description, Fields and ObjectsList."""
    assert objects(call, SplObjectMethods.OBJECTS)["data"] == {"string-0": "Memory"}
    description = objects(call, SplObjectMethods.DESC, {"type": "Memory"})
    assert description["result"] == "1"
    assert description["data"]["icon"] == "fa fa-flask"
    fields = objects(call, SplObjectMethods.FIELDS, {"type": "Memory"})
    assert fields["data"]["sku_lines"]["type"] == "varchar@list"
    listed = objects(call, SplObjectMethods.LIST, {"type": "Memory", "filters": "", "params": ""})
    assert listed["result"] == "1"
    assert listed["data"] == {"meta": {"current": "0", "total": "0"}}


def test_objects_crud(call: Call) -> None:
    """Set (create & update), Get, Identify and Delete."""
    created = objects(call, SplObjectMethods.SET, {"type": "Memory", "id": "", "fields": {"name": "Bob"}})
    assert (created["result"], created["data"]) == ("1", "1")
    updated = objects(call, SplObjectMethods.SET, {"type": "Memory", "id": "1", "fields": {"count": "3"}})
    assert updated["data"] == "1"
    read = objects(call, SplObjectMethods.GET, {"type": "Memory", "id": "1", "fields": ["name", "count"]})
    assert read["data"] == {"id": "1", "name": "Bob", "count": "3"}
    found = objects(call, SplObjectMethods.IDENTIFY, {"type": "Memory", "keys": {"name": "Bob"}})
    assert (found["result"], found["data"]) == ("1", "1")
    missing = objects(call, SplObjectMethods.IDENTIFY, {"type": "Memory", "keys": {"name": "Nobody"}})
    assert (missing["result"], missing["data"]) == ("1", "")
    assert objects(call, SplObjectMethods.DEL, {"type": "Memory", "id": "1"})["result"] == "1"
    gone = objects(call, SplObjectMethods.GET, {"type": "Memory", "id": "1", "fields": ["name"]})
    assert gone["result"] == "0"


@pytest.mark.parametrize(
    ("name", "params", "error"),
    [
        (SplObjectMethods.DESC, None, "Missing Task Parameters"),
        (SplObjectMethods.DESC, {"id": "1"}, "Missing Object Type"),
        (SplObjectMethods.DESC, {"type": "Unknown"}, "Object Type is Invalid"),
        (SplObjectMethods.GET, {"type": "Memory", "fields": ["name"]}, "Object Id is empty"),
        (SplObjectMethods.GET, {"type": "Memory", "id": "-2", "fields": ["name"]}, "Object Id is negative"),
        (SplObjectMethods.GET, {"type": "Memory", "id": {"a": "b"}, "fields": ["name"]}, "Object Id is invalid"),
        (SplObjectMethods.GET, {"type": "Memory", "id": "1", "fields": ""}, "requires an object id"),
        (SplObjectMethods.SET, {"type": "Memory", "id": "1", "fields": ""}, "requires a fields list"),
        ("Unknown", {"type": "Memory"}, "Requested task not found"),
    ],
)
def test_objects_errors(call: Call, name: str, params: Any, error: str) -> None:
    """Invalid tasks fail with an explicit error."""
    response = objects(call, name, params)
    assert response["result"] == "0"
    assert error in str(response["log"]["err"])


def test_objects_edge_cases(call: Call) -> None:
    """Commit task is only a warning; deleting without id fails; identify without keys returns nothing."""
    commit = objects(call, SplObjectMethods.COMMIT, {"type": "Memory"})
    assert commit["result"] == "0"
    assert "Commit" in str(commit["log"]["war"])
    assert objects(call, SplObjectMethods.DEL, {"type": "Memory", "id": ""})["result"] == "0"
    assert objects(call, SplObjectMethods.IDENTIFY, {"type": "Memory", "keys": ""})["data"] == ""


# ====================================================================#
# Widgets & Files
# ====================================================================#


def test_widgets(call: Call) -> None:
    """Widgets list, description and contents; disabled and unknown widgets."""
    listed = call(SplServices.WIDGETS, SplWidgetsMethods.LIST)
    assert listed["data"] == {"string-0": "Hello"}
    described = call(SplServices.WIDGETS, SplWidgetsMethods.DEFINITION, {"type": "Hello"})
    assert described["data"]["parameters"]["since"]["type"] == "date"
    contents = call(SplServices.WIDGETS, SplWidgetsMethods.GET, {"type": "Hello", "params": {"who": "Bob"}})
    assert contents["data"]["blocks"]["array-0"]["data"]["text"] == "Hello Bob"
    failed = call(SplServices.WIDGETS, SplWidgetsMethods.GET, {"type": "Hello", "params": {"fail": "1"}})
    assert failed["result"] == "0"
    for widget_type in ("Hidden", "Unknown"):
        assert call(SplServices.WIDGETS, SplWidgetsMethods.DEFINITION, {"type": widget_type})["result"] == "0"
    assert call(SplServices.WIDGETS, "Other")["result"] == "0"


def test_files(call: Call, memory: Memory) -> None:
    """Files are read from objects, by path and md5."""
    memory.files["/files/a.txt"] = b"content"
    md5 = Files.md5(b"content")
    exists = call(SplServices.FILES, SplFilesMethods.EXISTS, {"path": "/files/a.txt", "md5": md5})
    assert exists["data"] == "1"
    read = call(SplServices.FILES, SplFilesMethods.GET, {"file": "/files/a.txt", "md5": md5})
    assert read["data"]["raw"] == "Y29udGVudA=="
    assert call(SplServices.FILES, SplFilesMethods.GET, {"path": "/files/a.txt", "md5": "bad"})["result"] == "0"
    assert call(SplServices.FILES, SplFilesMethods.SET, {"path": "/x", "md5": "y"})["result"] == "0"
    assert call(SplServices.FILES, SplFilesMethods.GET, {"path": "/x"})["result"] == "0"
