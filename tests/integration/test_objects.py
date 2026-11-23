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

"""Objects layer: pipeline, reads, writes, phases, locks, extensions and commits."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from splashpy import SplashClient, SplashConfig
from splashpy.dictionary import SplOperations
from splashpy.fields import FieldsFactory, FieldType
from splashpy.objects import BaseObject, CommitEvent, ObjectRequest, PipelineError
from splashpy.objects.handler import ObjectHandler
from tests import support
from tests.support import JOURNAL, CoreGroup, Memory, Recorder


class Transport:
    """Fake Splash server accepting every call."""

    def __init__(self) -> None:
        """Record calls."""
        self.calls = 0

    def post(self, url: str, body: bytes, headers: Mapping[str, str], timeout: float) -> bytes:
        """Answer with a nil response: commit calls fail, which is enough to count them."""
        self.calls += 1
        return b""


@pytest.fixture
def memory() -> Memory:
    """Build a fresh in-memory object."""
    JOURNAL.clear()
    return Memory()


@pytest.fixture
def recorder() -> Recorder:
    """Build a recording extension."""
    return Recorder()


@pytest.fixture
def transport() -> Transport:
    """Build a fake transport."""
    return Transport()


@pytest.fixture
def mclient(config: SplashConfig, memory: Memory, recorder: Recorder, transport: Transport) -> SplashClient:
    """Build a client exposing the memory object."""
    return SplashClient(config, objects=[memory], extensions=[recorder], transport=transport)


@pytest.fixture
def handler(mclient: SplashClient) -> ObjectHandler:
    """Get the memory object handler."""
    found = mclient.object_handler("Memory")
    assert found is not None
    return found


# ====================================================================#
# Pipeline & Definitions
# ====================================================================#


def test_pipeline_order_and_origin(handler: ObjectHandler, mclient: SplashClient) -> None:
    """Groups are ordered by dependencies, then priority; extension groups are included."""
    steps = handler.describe_pipeline(mclient.new_context())
    assert [step["code"] for step in steps] == ["core", "details", "lines", "update_only", "tags"]
    assert steps[4]["origin"] == "recorder"
    assert steps[2]["fields"] == ["sku@lines", "qty@lines"]


def test_describe_and_fields_with_configurators(handler: ObjectHandler, mclient: SplashClient) -> None:
    """Extensions override description and fields."""
    ctx = mclient.new_context()
    assert handler.describe(ctx)["icon"] == "fa fa-flask"
    fields = handler.fields(ctx)
    assert list(fields) == ["name", "notes", "count", "sku@lines", "qty@lines", "late", "tags"]
    assert fields["notes"]["notest"] is True


@pytest.mark.parametrize(
    ("groups", "message"),
    [
        ((CoreGroup, CoreGroup), "declared twice"),
        ((support.DetailsGroup,), "unknown group"),
    ],
)
def test_pipeline_errors_at_build(config: SplashConfig, groups: Any, message: str) -> None:
    """Inconsistent groups fail when the client is built."""

    class Broken(Memory):
        pass

    Broken.groups = groups
    with pytest.raises(PipelineError, match=message):
        SplashClient(config, objects=[Broken()])


def test_duplicate_fields_and_shared_lists(config: SplashConfig) -> None:
    """A field defined by two groups, or a list shared by two groups, fails at build."""

    class Again(support.MemoryGroup):
        code = "again"

        def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
            factory.create(FieldType.VARCHAR, "name", "Again")

    class SharedList(support.MemoryGroup):
        code = "shared"

        def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
            factory.create(FieldType.VARCHAR, "other", "Other").in_list("lines")

    for extra in (Again, SharedList):

        class Broken(Memory):
            groups = (CoreGroup, support.LinesGroup, support.DetailsGroup, extra)

        with pytest.raises(PipelineError):
            SplashClient(config, objects=[Broken()])


def test_object_without_fields(config: SplashConfig) -> None:
    """An object without fields fails at build."""

    class Empty(Memory):
        groups = ()

    with pytest.raises(PipelineError, match="no fields"):
        SplashClient(config, objects=[Empty()])


def test_object_override_by_priority(config: SplashConfig) -> None:
    """The highest priority wins a type; equal priorities fail."""

    class Override(Memory):
        type = "Memory"
        priority = 200
        name = "Override"

    client = SplashClient(config, objects=[Memory(), Override()])
    handler = client.object_handler("Memory")
    assert handler is not None
    assert handler.describe(client.new_context())["name"] == "Override"
    with pytest.raises(PipelineError, match="provided twice"):
        SplashClient(config, objects=[Memory(), Memory()])


def test_disabled_objects_are_hidden(config: SplashConfig) -> None:
    """Disabled objects are neither listed nor served."""

    class Off(Memory):
        disabled = True

    client = SplashClient(config, objects=[Off()])
    assert client.object_types() == []
    assert client.object_handler("Off") is None


# ====================================================================#
# Write & Read
# ====================================================================#


def test_create_phases_and_read(handler: ObjectHandler, mclient: SplashClient, recorder: Recorder) -> None:
    """Create: CREATE groups first, then create(), then POST_CREATE groups, in pipeline order."""
    ctx = mclient.new_context()
    values = {"lines": {"array-0": {"sku": "A", "qty": "1"}}, "notes": "", "name": "Bob", "count": "3", "tags": "x"}
    new_id = handler.set(ctx, "", values)
    assert new_id == "1"
    assert JOURNAL == ["core:name", "core:name", "details:notes", "details:count", "lines:lines", "tags:tags"]
    assert recorder.events == ["before:Memory", "after:1"]
    data = handler.get(ctx, "1", ["name", "notes", "sku@lines", "qty@lines", "late"])
    assert data == {
        "id": "1",
        "name": "Bob",
        "notes": None,
        "lines": {"0": {"sku": "A", "qty": "1"}},
        "late": None,
    }


def test_update(handler: ObjectHandler, mclient: SplashClient, memory: Memory) -> None:
    """Update: UPDATE groups only; unchanged values do not save."""
    ctx = mclient.new_context()
    object_id = handler.set(ctx, None, {"name": "Bob"})
    assert object_id is not None
    assert handler.set(ctx, object_id, {"late": "now", "count": "2"}) == object_id
    assert memory.rows[object_id]["late"] == "now"


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ({"name": "Bob", "unknown": "x"}, "1"),
        ({"name": "Bob", "late": "x"}, "1"),
        ({"name": "Bob", "notes": "FAIL"}, "1"),
        ({"name": "Bob", "notes": "BOOM"}, "1"),
    ],
)
def test_create_failures_keep_new_id(handler: ObjectHandler, mclient: SplashClient, values: Any, expected: str) -> None:
    """Unknown, out of phase or failed fields fail the write, but a created id is returned."""
    ctx = mclient.new_context()
    assert handler.set(ctx, "", values) == expected
    assert ctx.logger.has_errors


def test_write_failures(handler: ObjectHandler, mclient: SplashClient, memory: Memory) -> None:
    """Missing objects, failed creations and failed updates return None."""
    ctx = mclient.new_context()
    assert handler.set(ctx, "404", {"name": "x"}) is None
    memory.fail_create = True
    assert handler.set(ctx, "", {"name": "x"}) is None
    memory.fail_create = False
    object_id = handler.set(ctx, "", {"name": "x"})
    memory.fail_update = True
    assert handler.set(ctx, str(object_id), {"notes": "changed"}) is None


def test_read_failures(handler: ObjectHandler, mclient: SplashClient, recorder: Recorder) -> None:
    """Missing objects, unknown fields and filtered objects fail reads."""
    ctx = mclient.new_context()
    object_id = str(handler.set(ctx, "", {"name": "x"}))
    assert handler.get(ctx, "404", ["name"]) is None
    assert handler.get(ctx, object_id, ["name", "unknown"]) is None
    recorder.filtered.add(object_id)
    assert handler.get(ctx, object_id, ["name"]) is None


def test_list_identify_delete(handler: ObjectHandler, mclient: SplashClient) -> None:
    """List with meta, identify by primary key, delete."""
    ctx = mclient.new_context()
    first = handler.set(ctx, "", {"name": "a"})
    handler.set(ctx, "", {"name": "b"})
    listed = handler.objects_list(ctx, None, {"max": "1", "offset": "1"})
    assert listed == {"0": {"id": "2", "name": "b"}, "meta": {"current": 1, "total": 2}}
    assert handler.identify(ctx, {"name": "a"}) == first
    assert handler.identify(ctx, {"name": "zz"}) is None
    assert handler.delete(ctx, str(first)) is True
    assert handler.get(ctx, str(first), ["name"]) is None


def test_default_list_meta(config: SplashConfig) -> None:
    """Lists always have meta, even when the object forgets it."""

    class NoMeta(Memory):
        def objects_list(self, ctx: Any, filter: str | None, params: Mapping[str, Any]) -> dict[str, Any]:
            return {}

    client = SplashClient(config, objects=[NoMeta()])
    handler = client.object_handler("NoMeta")
    assert handler is not None
    assert handler.objects_list(client.new_context(), "", {})["meta"] == {"current": 0, "total": 0}


# ====================================================================#
# Locks & Commits
# ====================================================================#


def test_commits_are_skipped_while_splash_writes(
    mclient: SplashClient, handler: ObjectHandler, recorder: Recorder, transport: Transport
) -> None:
    """A commit made by the host while Splash writes the object is not sent back."""

    class Committer(CoreGroup):
        def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
            mclient.commit("Memory", req.object_id or "new", SplOperations.UPDATE)
            mclient.commit("Memory", "1", SplOperations.CREATE)
            return super().set(req, field_id, value)

    handler.pipeline[0] = Committer()
    object_id = handler.set(mclient.new_context(), "", {"name": "x"})
    assert object_id == "1"
    assert transport.calls == 0
    assert [event.sent for event in recorder.commits] == [False] * 4  # create + post-create phases
    assert not mclient.locks.is_locked("Memory")


def test_commit_rules(mclient: SplashClient, recorder: Recorder, transport: Transport, monkeypatch: Any) -> None:
    """Unknown types, filtered or deleted objects and CI mode skip; others are sent."""
    assert mclient.commit("Unknown", 1, SplOperations.UPDATE) is True
    recorder.filtered.add("7")
    assert mclient.commit("Memory", 7, SplOperations.UPDATE) is True
    handler = mclient.object_handler("Memory")
    assert handler is not None
    handler.delete(mclient.new_context(), "8")
    assert mclient.commit("Memory", [8], SplOperations.DELETE) is True
    assert transport.calls == 0
    monkeypatch.setenv("SPLASH_CI", "1")
    assert mclient.commit("Memory", 9, SplOperations.UPDATE) is True
    monkeypatch.delenv("SPLASH_CI")
    assert mclient.commit("Memory", 9, SplOperations.UPDATE) is False
    assert transport.calls == 1
    assert [event.sent for event in mclient.commits] == [False, False, False, False]
    assert mclient.commits[-1] == CommitEvent("Memory", ("9",), "update")


def test_force_commit_skips_locks(handler: ObjectHandler, mclient: SplashClient) -> None:
    """When Splash forces commits, objects are not locked."""
    ctx = mclient.new_context()
    ctx.remote_server = {"forcecommit": "1"}
    assert handler.delete(ctx, "5") is True
    assert not mclient.locks.is_locked("Memory", "5")


def test_failing_extension_hooks_never_break(config: SplashConfig, memory: Memory) -> None:
    """Exceptions in filters, events and commit listeners are logged only."""

    class Broken(Recorder):
        name = "broken"

        def is_filtered(self, *args: Any) -> bool:
            raise RuntimeError("filter")

        def before_set(self, req: ObjectRequest) -> None:
            raise RuntimeError("event")

        def on_commit(self, *args: Any) -> None:
            raise RuntimeError("commit")

    client = SplashClient(config, objects=[memory], extensions=[Broken()], transport=Transport())
    handler = client.object_handler("Memory")
    assert handler is not None
    ctx = client.new_context()
    object_id = handler.set(ctx, "", {"name": "x"})
    assert handler.get(ctx, str(object_id), ["name"]) is not None
    assert "RuntimeError: event" in ctx.logger.entries("err")
    client.commit("Memory", 1, SplOperations.UPDATE)


def test_base_object_contract() -> None:
    """The base object must be implemented; optional hooks have defaults."""
    obj = BaseObject()
    req = ObjectRequest(ctx=None, object_type="X")  # type: ignore[arg-type]
    for call in (
        lambda: obj.load(req, "1"),
        lambda: obj.create(req),
        lambda: obj.object_id(req),
        lambda: obj.update(req, True),
        lambda: obj.delete(req.ctx, "1"),
        lambda: obj.objects_list(req.ctx, None, {}),
    ):
        with pytest.raises(NotImplementedError):
            call()
    assert obj.get_by_primary(req.ctx, {}) is None
    assert obj.read_file(req.ctx, "p", "m") is None
    assert obj.describe()["name"] == "BaseObject"
    assert BaseObject.list_params({"max": "x", "offset": "-3"}) == (25, 0)
