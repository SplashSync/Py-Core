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


"""Conformance checks of a Splash client, usable without pytest.

Each check returns the list of problems found (empty when conform), so a connector can run them
from any test runner. ``splashpy.testing.suite`` runs them as pytest tests.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Final

from splashpy.dictionary import SplOperations
from splashpy.fields import Lists
from splashpy.fields.field import to_tag
from splashpy.fields.types import FieldType, SyncMode
from splashpy.objects.pipeline import resolve
from splashpy.testing.values import ValuesGenerator, base_type, is_testable, same_value, wire

if TYPE_CHECKING:
    from splashpy.client import SplashClient
    from splashpy.core.context import RequestContext
    from splashpy.objects.events import CommitEvent

DESCRIPTION_KEYS: Final = (
    "type",
    "name",
    "description",
    "icon",
    "disabled",
    "allow_push_created",
    "allow_push_updated",
    "allow_push_deleted",
    "enable_push_created",
    "enable_push_updated",
    "enable_push_deleted",
    "enable_pull_created",
    "enable_pull_updated",
    "enable_pull_deleted",
)
"""Keys of an object description, in protocol order."""

FIELD_KEYS: Final = (
    "type", "id", "name", "desc", "group", "required", "read", "write", "index", "inlist", "hlist",
    "log", "primary", "syncmode", "itemtype", "itemprop", "tag", "choices", "asso", "options", "notest",
)  # fmt: skip
"""Keys of a field definition, in protocol order."""

FIELD_ID: Final = re.compile(r"^[A-Za-z0-9_\-]+(@[A-Za-z0-9_\-]+)?$")
"""Valid field identifier (``id`` or ``id@list``)."""


class NotApplicableError(Exception):
    """The check cannot run on this object (reason in the message)."""


# ====================================================================#
# Description & Fields
# ====================================================================#


def check_description(client: SplashClient, ctx: RequestContext, object_type: str) -> list[str]:
    """Check an object description."""
    handler = _handler(client, object_type)
    description = handler.describe(ctx)
    problems = [f"description key '{key}' is missing" for key in DESCRIPTION_KEYS if key not in description]
    if description.get("type") != object_type:
        problems.append(f"description type is {description.get('type')!r}")
    if not description.get("name"):
        problems.append("description name is empty")
    return problems


def check_fields(client: SplashClient, ctx: RequestContext, object_type: str) -> list[str]:
    """Check every field definition of an object."""
    fields = _handler(client, object_type).fields(ctx)
    if not fields:
        return ["object has no fields"]
    problems: list[str] = []
    for field_id, field in fields.items():
        problems.extend(f"{field_id}: {problem}" for problem in check_field(field_id, field))
    if ctx.logger.has_errors:
        problems.extend(ctx.logger.entries("err"))
    return problems


def check_field(field_id: str, field: Mapping[str, Any]) -> list[str]:
    """Check one field definition."""
    problems = [f"key '{key}' is missing" for key in FIELD_KEYS if key not in field]
    if problems:
        return problems
    if field["id"] != field_id or not FIELD_ID.match(field_id):
        problems.append(f"invalid identifier {field['id']!r}")
    kind = base_type(field)
    if kind not in FieldType.ALL:
        problems.append(f"unknown type {field['type']!r}")
    if Lists.is_list(field_id) != Lists.is_list(str(field["type"])):
        problems.append("list fields need a list type (and only them)")
    if not field["desc"]:
        problems.append("description is empty")
    if field["primary"] and kind not in FieldType.PRIMARY:
        problems.append(f"type {kind} cannot be primary")
    if field["syncmode"] not in SyncMode.ALL:
        problems.append(f"invalid sync mode {field['syncmode']!r}")
    if bool(field["itemtype"]) != bool(field["itemprop"]):
        problems.append("metadata needs both itemtype and itemprop")
    if field["itemtype"] and field["itemprop"] and field["tag"] != to_tag(field["itemtype"], field["itemprop"]):
        problems.append("tag does not match the metadata")
    if not field["read"] and not field["write"]:
        problems.append("field is neither readable nor writable")
    if field["required"] and not field["write"]:
        problems.append("required field is not writable")
    for choice in field["choices"]:
        if not isinstance(choice, Mapping) or not choice.get("key"):
            problems.append(f"invalid choice {choice!r}")
    return problems


def check_pipeline(client: SplashClient, ctx: RequestContext, object_type: str) -> list[str]:
    """Check the fields groups pipeline is deterministic (whatever the declaration order)."""
    handler = _handler(client, object_type)
    problems: list[str] = []
    if handler.describe_pipeline(ctx) != handler.describe_pipeline(ctx):
        problems.append("pipeline description changes between two builds")
    groups = list(handler.pipeline)
    expected = [group.group_code() for group in groups]
    for order in (list(reversed(groups)), groups[1:] + groups[:1]):
        if [group.group_code() for group in resolve(object_type, order)] != expected:
            problems.append("pipeline order depends on the groups declaration order")
            break
    return problems


# ====================================================================#
# CRUD & Lists
# ====================================================================#


def roundtrip(client: SplashClient, ctx: RequestContext, object_type: str, seed: int = 0) -> list[str]:
    """Create an object with generated values, read it back, update it, read it back, delete it.

    :raises NotApplicableError: when a required field cannot be generated.
    """
    handler = _handler(client, object_type)
    fields = handler.fields(ctx)
    untestable = [field_id for field_id, field in fields.items() if field["required"] and not is_testable(field)]
    if untestable:
        raise NotApplicableError(f"required fields cannot be generated: {', '.join(untestable)}")
    generator = ValuesGenerator(seed)
    problems: list[str] = []
    created = wire(generator.values(fields)) or {}
    object_id = handler.set(ctx, "", created)
    if not object_id:
        return [f"create failed: {ctx.logger.entries('err')}"]
    try:
        problems.extend(f"create: {problem}" for problem in _compare(handler, ctx, str(object_id), fields, created))
        updated = wire(generator.values(fields)) or {}
        if handler.set(ctx, str(object_id), updated) != str(object_id):
            problems.append("update did not return the object id")
        problems.extend(f"update: {problem}" for problem in _compare(handler, ctx, str(object_id), fields, updated))
        problems.extend(ctx.logger.entries("err"))
    finally:
        if not handler.delete(ctx, str(object_id)):
            problems.append("delete failed")
    if handler.get(client.new_context(), str(object_id), list(fields)[:1]):
        problems.append("object still readable after delete")
    return problems


def check_list(client: SplashClient, ctx: RequestContext, object_type: str, count: int = 3, seed: int = 1) -> list[str]:
    """Create objects, then check the objects list meta and pagination.

    :raises NotApplicableError: when a required field cannot be generated.
    """
    handler = _handler(client, object_type)
    fields = handler.fields(ctx)
    if any(field["required"] and not is_testable(field) for field in fields.values()):
        raise NotApplicableError("required fields cannot be generated")
    generator = ValuesGenerator(seed)
    created = [handler.set(ctx, "", wire(generator.values(fields)) or {}) for _ in range(count)]
    problems: list[str] = []
    try:
        everything = handler.objects_list(ctx, None, {"max": 1000, "offset": 0})
        meta = everything.get("meta") or {}
        if int(meta.get("total", 0)) < count or int(meta.get("current", 0)) < count:
            problems.append(f"list meta does not count the created objects: {meta}")
        first = _ids(handler.objects_list(ctx, None, {"max": 1, "offset": 0}))
        second = _ids(handler.objects_list(ctx, None, {"max": 1, "offset": 1}))
        if len(first) != 1 or len(second) != 1 or first == second:
            problems.append(f"pagination does not work: {first} then {second}")
    finally:
        for object_id in created:
            if object_id:
                handler.delete(ctx, str(object_id))
    return problems


# ====================================================================#
# Commits
# ====================================================================#


@contextmanager
def expect_commit(client: SplashClient, object_type: str, action: str = SplOperations.UPDATE) -> Iterator[None]:
    """Check the host application commits an object while the block runs (native changes).

    :raises AssertionError: when no commit of this type and action was emitted.
    """
    before = len(client.commits)
    yield
    events: list[CommitEvent] = client.commits[before:]
    if not any(event.type == object_type and event.action == action for event in events):
        raise AssertionError(f"No {action} commit of {object_type} was emitted ({len(events)} other commits).")


# ====================================================================#
# Private Functions
# ====================================================================#


def _handler(client: SplashClient, object_type: str) -> Any:
    """Get an object handler."""
    handler = client.object_handler(object_type)
    if handler is None:
        raise NotApplicableError(f"unknown object type {object_type}")
    return handler


def _compare(handler: Any, ctx: RequestContext, object_id: str, fields: Mapping[str, Any], sent: Any) -> list[str]:
    """Read an object and compare its values with what was sent."""
    received = wire(handler.get(ctx, object_id, list(fields)) or {}) or {}
    problems: list[str] = []
    for field_id, field in fields.items():
        if not is_testable(field):
            continue
        parts = Lists.explode(field_id)
        if parts is None:
            if not same_value(field, sent.get(field_id), received.get(field_id)):
                problems.append(f"{field_id}: sent {sent.get(field_id)!r}, received {received.get(field_id)!r}")
            continue
        sent_items = list((sent.get(parts[1]) or {}).values())
        received_items = list((received.get(parts[1]) or {}).values())
        if len(sent_items) != len(received_items):
            problems.append(f"{parts[1]}: sent {len(sent_items)} items, received {len(received_items)}")
            continue
        for index, (sent_item, received_item) in enumerate(zip(sent_items, received_items)):
            if not same_value(field, sent_item.get(parts[0]), received_item.get(parts[0])):
                problems.append(
                    f"{field_id}[{index}]: sent {sent_item.get(parts[0])!r}, received {received_item.get(parts[0])!r}"
                )
    return problems


def _ids(listed: Mapping[str, Any]) -> list[str]:
    """Get the identifiers of an objects list."""
    return [str(item.get("id")) for key, item in listed.items() if key != "meta" and isinstance(item, Mapping)]
