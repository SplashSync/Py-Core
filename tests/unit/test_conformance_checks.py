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


"""Conformance checks find problems: broken definitions, values, lists, pipelines and commits."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

import pytest

from splashpy import SplashClient, SplashConfig
from splashpy.core.context import RequestContext
from splashpy.dictionary import SplOperations
from splashpy.fields import FieldsFactory, FieldType, Prices
from splashpy.objects import BaseObject, FieldsGroup, ObjectRequest, fields_group
from splashpy.testing import (
    NotApplicableError,
    ValuesGenerator,
    check_description,
    check_field,
    check_fields,
    check_list,
    check_pipeline,
    expect_commit,
    roundtrip,
    same_value,
    wire,
)


@fields_group("core")
class SloppyCore(FieldsGroup):
    """Stores the code in upper case: a round trip bug."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare fields."""
        factory.create(FieldType.VARCHAR, "name", "Name").is_required()
        factory.create(FieldType.VARCHAR, "code", "Code")
        factory.create(FieldType.INT, "qty", "Quantity")

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read a value."""
        return req.object.get(field_id)

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool:
        """Write a value (the code in upper case)."""
        req.object[field_id] = value.upper() if field_id == "code" and value else value
        req.need_update()
        return True


class Sloppy(BaseObject):
    """In-memory object with bugs to find."""

    groups: ClassVar = (SloppyCore,)
    paginate: ClassVar[bool] = True
    rows: ClassVar[dict[str, dict[str, Any]]] = {}

    def load(self, req: ObjectRequest, object_id: str) -> Any:
        """Load a row."""
        return self.rows.get(object_id)

    def create(self, req: ObjectRequest) -> Any:
        """Create a row."""
        row = {"_id": str(len(self.rows) + 1)}
        self.rows[row["_id"]] = row
        return row

    def object_id(self, req: ObjectRequest) -> str | None:
        """Get the row id."""
        return str(req.object["_id"])

    def update(self, req: ObjectRequest, needed: bool) -> str | None:
        """Rows are updated in place."""
        return str(req.object["_id"])

    def delete(self, ctx: RequestContext, object_id: str) -> bool:
        """Delete a row."""
        self.rows.pop(object_id, None)
        return True

    def objects_list(self, ctx: RequestContext, filter: str | None, params: Mapping[str, Any]) -> dict[str, Any]:
        """List rows (pagination can be broken)."""
        limit, offset = self.list_params(params)
        rows = list(self.rows.values())[offset : offset + limit] if self.paginate else list(self.rows.values())
        return self.list_result([{"id": row["_id"]} for row in rows], len(self.rows))


@pytest.fixture
def sloppy(config: SplashConfig) -> SplashClient:
    """Client exposing the sloppy object."""
    Sloppy.rows = {}
    Sloppy.paginate = True
    return SplashClient(config, objects=[Sloppy])


FIELD: dict[str, Any] = {
    "type": "varchar", "id": "code", "name": "Code", "desc": "Code", "group": None, "required": False,
    "read": True, "write": True, "index": False, "inlist": False, "hlist": False, "log": False,
    "primary": False, "syncmode": "both", "itemtype": None, "itemprop": None, "tag": None,
    "choices": [], "asso": [], "options": {}, "notest": False,
}  # fmt: skip
"""A valid field definition."""


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"id": "other"}, "invalid identifier"),
        ({"type": "unknown"}, "unknown type"),
        ({"type": "varchar@list"}, "list fields need a list type"),
        ({"desc": ""}, "description is empty"),
        ({"type": "bool", "primary": True}, "cannot be primary"),
        ({"syncmode": "sometimes"}, "invalid sync mode"),
        ({"itemtype": "http://schema.org/Thing"}, "needs both itemtype and itemprop"),
        ({"itemtype": "http://schema.org/Thing", "itemprop": "name", "tag": "x"}, "tag does not match"),
        ({"read": False, "write": False}, "neither readable nor writable"),
        ({"required": True, "write": False}, "required field is not writable"),
        ({"choices": [{"value": "No key"}]}, "invalid choice"),
    ],
)
def test_check_field_problems(change: dict[str, Any], problem: str) -> None:
    """Every kind of broken definition is reported."""
    assert check_field("code", FIELD) == []
    assert any(problem in found for found in check_field("code", {**FIELD, **change}))


def test_checks_find_object_problems(sloppy: SplashClient) -> None:
    """Round trip differences and broken pagination are reported; valid parts pass."""
    ctx = sloppy.new_context()
    assert check_description(sloppy, ctx, "Sloppy") == []
    assert check_fields(sloppy, ctx, "Sloppy") == []
    assert check_pipeline(sloppy, ctx, "Sloppy") == []
    assert check_field("code", {"id": "code"})[0] == "key 'type' is missing"
    problems = roundtrip(sloppy, ctx, "Sloppy")
    assert any(problem.startswith("create: code: sent") for problem in problems)
    assert check_list(sloppy, sloppy.new_context(), "Sloppy") == []
    Sloppy.paginate = False
    assert any("pagination" in problem for problem in check_list(sloppy, sloppy.new_context(), "Sloppy"))
    with pytest.raises(NotApplicableError, match="unknown object type"):
        check_description(sloppy, ctx, "Missing")


def test_checks_skip_objects_with_required_links(config: SplashConfig) -> None:
    """Objects needing a link to another object cannot be generated: the check is not applicable."""

    @fields_group("core")
    class Linked(SloppyCore):
        def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
            factory.create(FieldType.VARCHAR, "name", "Name")
            factory.create(FieldType.object_id("Sloppy"), "parent", "Parent").is_required()

    class Child(Sloppy):
        groups: ClassVar = (Linked,)

    client = SplashClient(config, objects=[Child])
    with pytest.raises(NotApplicableError, match="parent"):
        roundtrip(client, client.new_context(), "Child")
    with pytest.raises(NotApplicableError):
        check_list(client, client.new_context(), "Child")


def test_check_pipeline_problems(sloppy: SplashClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unstable pipelines are reported."""
    handler = sloppy.object_handler("Sloppy")
    assert handler is not None
    counter = iter(range(10))
    monkeypatch.setattr(handler, "describe_pipeline", lambda ctx: [next(counter)])
    monkeypatch.setattr("splashpy.testing.checks.resolve", lambda object_type, groups: [])
    problems = check_pipeline(sloppy, sloppy.new_context(), "Sloppy")
    assert len(problems) == 2


def test_expect_commit(sloppy: SplashClient) -> None:
    """Commits emitted by the host application are expected."""
    with expect_commit(sloppy, "Sloppy", SplOperations.UPDATE):
        sloppy.commit("Sloppy", "1", SplOperations.UPDATE)
    with pytest.raises(AssertionError, match="No delete commit"), expect_commit(sloppy, "Sloppy", SplOperations.DELETE):
        sloppy.commit("Sloppy", "1", SplOperations.UPDATE)


def test_values_and_comparators() -> None:
    """Generated values respect choices and lengths; comparators follow the field type."""
    generator = ValuesGenerator(3)
    assert generator.value({**FIELD, "choices": [{"key": "a", "value": "A"}]}) == "a"
    assert len(generator.value({**FIELD, "options": {"maxLength": 3}})) == 3
    rows = generator.values({"label@items": {**FIELD, "id": "label@items", "type": "varchar@list"}}, items=3)
    assert len(rows["items"]) == 3
    assert generator.values({"code": {**FIELD, "notest": True}}) == {}
    for kind, sent, received, same in [
        ("bool", "1", "1", True),
        ("bool", "1", "0", False),
        ("int", "12", "12.0", True),
        ("double", "1.5", "1.50000001", True),
        ("double", "1.5", "x", False),
        ("date", "2026-01-02", "2026-01-02 10:00:00", True),
        ("datetime", "2026-01-02 10:00:00", "2026-01-02 10:00:01", False),
        ("inline", '["a","b"]', '["b","a"]', True),
        ("varchar", "", None, True),
        ("varchar", "a", None, False),
        ("objectid::Product", "1::Product", "1::Product", True),
    ]:
        assert same_value({"type": kind}, sent, received) is same, (kind, sent, received)
    price = wire(Prices.encode(10.0, 20.0, code="EUR"))
    assert same_value({"type": "price"}, price, price)
    assert wire(None) == ""
