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

"""In-memory test objects, fields groups, extensions and widgets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from splashpy import Extension, RequestContext
from splashpy.fields import FieldsFactory, FieldType, Files, Lists
from splashpy.objects import BaseObject, CommitEvent, FieldsGroup, ObjectRequest, Phase, fields_group
from splashpy.widgets import BaseWidget, WidgetRender

JOURNAL: list[str] = []
"""Calls journal, to check groups order."""


class MemoryGroup(FieldsGroup):
    """Store owned values in a dict object, journaling writes."""

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read a value (lists: one value per item)."""
        parts = Lists.explode(field_id)
        if parts is None:
            return req.object.get(field_id)
        return [item.get(parts[0]) for item in req.object.get(parts[1]) or []]

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
        """Write a value."""
        JOURNAL.append(f"{self.group_code()}:{field_id}")
        if value == "FAIL":
            return False
        if value == "BOOM":
            raise RuntimeError("group failure")
        if req.object is None:
            req.stash[field_id] = value
            return True
        if req.object.get(field_id) != value:
            req.object[field_id] = value
            req.need_update()
        return True


@fields_group("core", priority=10, phases=Phase.ALL)
class CoreGroup(MemoryGroup):
    """Required name, written before creation too."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare fields."""
        factory.create(FieldType.VARCHAR, "name", "Name").is_required().is_primary().is_listed()


@fields_group("details", priority=5, after=("core",))
class DetailsGroup(MemoryGroup):
    """Details, after core despite a lower priority."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare fields."""
        factory.create(FieldType.TEXT, "notes", "Notes")
        factory.create(FieldType.INT, "count", "Count")


@fields_group("lines", priority=50, after=("details",), phases=(Phase.POST_CREATE, Phase.UPDATE))
class LinesGroup(MemoryGroup):
    """A list of lines."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare fields."""
        factory.create(FieldType.VARCHAR, "sku", "SKU").in_list("lines")
        factory.create(FieldType.INT, "qty", "Qty").in_list("lines")


@fields_group("update_only", priority=60, phases=(Phase.UPDATE,))
class UpdateOnlyGroup(MemoryGroup):
    """Only writable on existing objects."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare fields."""
        factory.create(FieldType.VARCHAR, "late", "Late")


class Memory(BaseObject):
    """In-memory object."""

    name = "Memory"
    groups: ClassVar[Sequence[type[FieldsGroup]]] = (LinesGroup, UpdateOnlyGroup, DetailsGroup, CoreGroup)

    def __init__(self) -> None:
        """Create an empty store."""
        self.rows: dict[str, dict[str, Any]] = {}
        self.files: dict[str, bytes] = {}
        self.next_id = 1
        self.fail_create = False
        self.fail_update = False

    def load(self, req: ObjectRequest, object_id: str) -> Any:
        """Load a row."""
        row = self.rows.get(object_id)
        return dict(row) if row is not None else None

    def create(self, req: ObjectRequest) -> Any:
        """Create a row from stashed values."""
        if self.fail_create:
            return None
        object_id = str(self.next_id)
        self.next_id += 1
        self.rows[object_id] = {"name": req.stash.get("name"), "_id": object_id}
        return dict(self.rows[object_id])

    def object_id(self, req: ObjectRequest) -> str | None:
        """Get the row id."""
        return str(req.object["_id"])

    def update(self, req: ObjectRequest, needed: bool) -> str | None:
        """Save the row."""
        if self.fail_update:
            return None
        if needed:
            self.rows[str(req.object["_id"])] = dict(req.object)
        return str(req.object["_id"])

    def delete(self, ctx: RequestContext, object_id: str) -> bool:
        """Delete a row."""
        self.rows.pop(object_id, None)
        return True

    def objects_list(self, ctx: RequestContext, filter: str | None, params: Mapping[str, Any]) -> dict[str, Any]:
        """List rows."""
        limit, offset = self.list_params(params)
        rows = list(self.rows.values())
        items = [{"id": row["_id"], "name": row.get("name")} for row in rows[offset : offset + limit]]
        return self.list_result(items, len(rows))

    def get_by_primary(self, ctx: RequestContext, keys: Mapping[str, str]) -> str | None:
        """Find by name."""
        matches = [row["_id"] for row in self.rows.values() if row.get("name") == keys.get("name")]
        return matches[0] if len(matches) == 1 else None

    def read_file(self, ctx: RequestContext, path: str, md5: str) -> dict[str, Any] | None:
        """Read a stored file."""
        raw = self.files.get(path)
        if raw is None or Files.md5(raw) != md5:
            return None
        return Files.read(path, raw)


class TagsGroup(MemoryGroup):
    """Extension group adding a field to Memory."""

    code = "tags"
    after: ClassVar[tuple[str, ...]] = ("core",)

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare fields."""
        factory.create(FieldType.VARCHAR, "tags", "Tags")


class Hello(BaseWidget):
    """Test widget."""

    name = "Hello"

    def build_parameters(self, factory: FieldsFactory, ctx: RequestContext) -> None:
        """Declare one parameter."""
        factory.create(FieldType.DATE, "since", "Since")

    def render(self, ctx: RequestContext, params: Mapping[str, Any], output: WidgetRender) -> bool | None:
        """Render a text, or fail on demand."""
        if params.get("fail"):
            return False
        output.blocks.add_text_block(f"Hello {params.get('who', 'World')}")
        return True


class Hidden(Hello):
    """Disabled widget."""

    disabled = True


class Recorder(Extension):
    """Extension recording events, adding a group, a filter and configurators."""

    name = "recorder"

    def __init__(self) -> None:
        """Start empty journals."""
        self.events: list[str] = []
        self.commits: list[CommitEvent] = []
        self.filtered: set[str] = set()

    def fields_groups(self) -> Mapping[str, Sequence[type[FieldsGroup]]]:
        """Add tags to Memory."""
        return {"Memory": (TagsGroup,)}

    def widgets(self) -> Sequence[BaseWidget | type[BaseWidget]]:
        """Provide widgets."""
        return (Hello, Hidden)

    def is_filtered(self, ctx: RequestContext, object_type: str, object_id: str, obj: Any) -> bool:
        """Hide filtered ids."""
        return object_id in self.filtered

    def configure_description(self, ctx: RequestContext, object_type: str, description: dict[str, Any]) -> None:
        """Change the icon."""
        description["icon"] = "fa fa-flask"

    def configure_fields(self, ctx: RequestContext, object_type: str, fields: dict[str, dict[str, Any]]) -> None:
        """Mark notes as not tested."""
        if "notes" in fields:
            fields["notes"]["notest"] = True

    def before_set(self, req: ObjectRequest) -> None:
        """Record."""
        self.events.append(f"before:{req.object_type}")

    def after_set(self, req: ObjectRequest, object_id: str | None) -> None:
        """Record."""
        self.events.append(f"after:{object_id}")

    def on_commit(self, ctx: RequestContext, event: CommitEvent) -> None:
        """Record."""
        self.commits.append(event)
