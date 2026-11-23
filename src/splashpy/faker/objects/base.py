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

"""Base of faker objects: CRUD on the faker store, and stored fields helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from splashpy.core.context import RequestContext
from splashpy.faker.store import FakerStore, Record
from splashpy.fields import Lists
from splashpy.objects import BaseObject, FieldsGroup, ObjectRequest


class StoredGroup(FieldsGroup):
    """Base of faker fields groups: values live in the stored document."""

    @staticmethod
    def record(req: ObjectRequest) -> Record:
        """Get the faker record of a request."""
        record = req.object
        if not isinstance(record, Record):
            raise TypeError("Faker object is not loaded.")
        return record

    @classmethod
    def read(cls, req: ObjectRequest, field_id: str) -> Any:
        """Read a stored value (lists: one value per item)."""
        data = cls.record(req).data
        parts = Lists.explode(field_id)
        if parts is None:
            return data.get(field_id)
        return [item.get(parts[0]) for item in data.get(parts[1]) or [] if isinstance(item, Mapping)]

    @classmethod
    def write(cls, req: ObjectRequest, field_id: str, value: Any) -> bool:
        """Store a value when it changed."""
        data = cls.record(req).data
        if data.get(field_id) != value:
            data[field_id] = value
            req.need_update()
        return True


class FakerObject(BaseObject):
    """Faker object: CRUD on the faker store."""

    listed_fields: ClassVar[Sequence[str]] = ("name",)
    """Ids of the fields returned in lists."""

    def __init__(self, store: FakerStore) -> None:
        """Use a faker store."""
        self.store = store

    def load(self, req: ObjectRequest, object_id: str) -> Any:
        """Load a record."""
        return self.store.load(self.object_type(), object_id)

    def create(self, req: ObjectRequest) -> Any:
        """Create an empty record (groups write the values next)."""
        return self.store.create(self.object_type())

    def object_id(self, req: ObjectRequest) -> str | None:
        """Get the record id."""
        return StoredGroup.record(req).id

    def update(self, req: ObjectRequest, needed: bool) -> str | None:
        """Save the record."""
        record = StoredGroup.record(req)
        if needed and not self.store.save(self.object_type(), record):
            return None
        return record.id

    def delete(self, ctx: RequestContext, object_id: str) -> bool:
        """Delete a record."""
        self.store.delete(self.object_type(), object_id)
        return True

    def objects_list(self, ctx: RequestContext, filter: str | None, params: Mapping[str, Any]) -> dict[str, Any]:
        """List records, with listed fields."""
        records = self.store.all(self.object_type())
        if filter:
            records = [record for record in records if filter.lower() in str(record.data).lower()]
        limit, offset = self.list_params(params)
        items = [
            {"id": record.id, **{field: record.data.get(field) for field in self.listed_fields}}
            for record in records[offset : offset + limit]
        ]
        return self.list_result(items, len(records))
