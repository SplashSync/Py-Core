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

"""Runtime of one object type: the Php-Core object algorithms over the ordered pipeline.

Each field id (or list name) is owned by exactly one fields group: reads and writes
are routed to it, in pipeline order. Inconsistent definitions are reported when the
client is built.
"""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from splashpy.core.context import RequestContext
from splashpy.extensions import Extension
from splashpy.fields import FieldsFactory, ObjectField
from splashpy.fields.helpers import Lists
from splashpy.objects.base import BaseObject
from splashpy.objects.group import FieldsGroup, Phase
from splashpy.objects.locks import Locks
from splashpy.objects.pipeline import PipelineError, resolve
from splashpy.objects.request import ObjectRequest


@dataclass
class Ownership:
    """Fields built for one request, and the group owning each of them."""

    fields: dict[str, ObjectField] = field(default_factory=dict)
    """Field definitions, by id."""

    fields_owner: dict[str, FieldsGroup] = field(default_factory=dict)
    """Owner of each field id."""

    lists_owner: dict[str, FieldsGroup] = field(default_factory=dict)
    """Owner of each list name."""

    errors: list[str] = field(default_factory=list)
    """Ownership errors (duplicates, lists shared by groups...)."""


class ObjectHandler:
    """Serve one object type for a client."""

    # ====================================================================#
    # Constructor
    # ====================================================================#

    def __init__(self, obj: BaseObject, extensions: Sequence[Extension], locks: Locks, origin: str = "core") -> None:
        """Resolve the pipeline of an object: its own groups plus extension groups.

        :raises PipelineError: when groups cannot be ordered.
        """
        self.object = obj
        self.type = obj.object_type()
        self.origin = origin
        self.extensions = tuple(extensions)
        self.locks = locks
        groups: list[FieldsGroup] = []
        for group_class in obj.groups:
            groups.append(group_class())
        for extension in self.extensions:
            for group_class in extension.fields_groups().get(self.type, ()):
                group = group_class()
                group.origin = extension.name or type(extension).__name__
                groups.append(group)
        self.pipeline = resolve(self.type, groups)

    # ====================================================================#
    # Definition
    # ====================================================================#

    def describe(self, ctx: RequestContext) -> dict[str, Any]:
        """Object description, with extensions overrides."""
        description = self.object.describe()
        for extension in self.extensions:
            extension.configure_description(ctx, self.type, description)
        return description

    def fields(self, ctx: RequestContext) -> dict[str, dict[str, Any]]:
        """Get published fields definitions, with extensions overrides."""
        ownership = self.build(ObjectRequest(ctx, self.type))
        for error in ownership.errors:
            ctx.logger.error(error)
        published = {field_id: definition.to_dict() for field_id, definition in ownership.fields.items()}
        for extension in self.extensions:
            extension.configure_fields(ctx, self.type, published)
        return published

    def build(self, req: ObjectRequest) -> Ownership:
        """Build every group fields and record who owns what."""
        ownership = Ownership()
        factory = FieldsFactory()
        for group in self.pipeline:
            known = {field_id: id(definition) for field_id, definition in factory.fields().items()}
            group.build(factory, req)
            for field_id, definition in factory.fields().items():
                if known.get(field_id) == id(definition):
                    continue
                if field_id in known:
                    ownership.errors.append(f"{self.type}: field '{field_id}' is defined twice.")
                ownership.fields[field_id] = definition
                ownership.fields_owner[field_id] = group
                list_name = Lists.list_name(field_id)
                if list_name is None:
                    continue
                owner = ownership.lists_owner.setdefault(list_name, group)
                if owner is not group:
                    ownership.errors.append(
                        f"{self.type}: list '{list_name}' is shared by groups "
                        f"'{owner.group_code()}' and '{group.group_code()}'."
                    )
        for error in factory.errors:
            ownership.errors.append(f"{self.type}: {error}")
        return ownership

    def validate(self, ctx: RequestContext) -> None:
        """Check fields definitions once, when the client is built.

        :raises PipelineError: on duplicate fields, shared lists or no fields at all.
        """
        ownership = self.build(ObjectRequest(ctx, self.type))
        duplicates = [error for error in ownership.errors if "twice" in error or "shared" in error]
        if duplicates:
            raise PipelineError(" ".join(duplicates))
        if not ownership.fields:
            raise PipelineError(f"{self.type}: object has no fields.")

    def describe_pipeline(self, ctx: RequestContext) -> list[dict[str, Any]]:
        """Describe the resolved pipeline: groups in order, with their position rules and owned fields."""
        ownership = self.build(ObjectRequest(ctx, self.type))
        return [
            {
                "code": group.group_code(),
                "priority": group.priority,
                "after": list(group.after),
                "before": list(group.before),
                "phases": list(group.phases),
                "origin": group.origin,
                "fields": [field_id for field_id, owner in ownership.fields_owner.items() if owner is group],
            }
            for group in self.pipeline
        ]

    # ====================================================================#
    # Read
    # ====================================================================#

    def get(self, ctx: RequestContext, object_id: str, field_ids: Sequence[str]) -> dict[str, Any] | None:
        """Read fields of an object; None (task failure) if any field cannot be read."""
        req = ObjectRequest(ctx, self.type, object_id=object_id)
        req.object = self.object.load(req, object_id)
        if req.object is None:
            ctx.logger.error(f"{self.type}: unable to load object {object_id}.")
            return None
        if self.is_filtered(ctx, object_id, req.object):
            ctx.logger.error(f"{self.type}: object {object_id} is filtered by an extension.")
            return None
        ownership = self.build(req)
        output: dict[str, Any] = {"id": object_id}
        missing: list[str] = []
        for field_id in field_ids:
            owner = ownership.fields_owner.get(field_id)
            if owner is None:
                missing.append(field_id)
                continue
            value = owner.get(req, field_id)
            parts = Lists.explode(field_id)
            if parts is None:
                output[field_id] = value
                continue
            items = output.setdefault(parts[1], {})
            for index, item_value in enumerate(_values(value)):
                items.setdefault(str(index), {})[parts[0]] = item_value
        for field_id in missing:
            ctx.logger.error(f"{self.type}: requested field not found => {field_id}")
        return None if missing else output

    # ====================================================================#
    # Write
    # ====================================================================#

    def set(self, ctx: RequestContext, object_id: str | None, values: Mapping[str, Any]) -> str | None:
        """Create (no id) or update an object; return its id, None on failure.

        The object is locked while written (a created object is locked as ``new``, then by
        its new id), so changes made meanwhile by the host application are not committed back.
        """
        inputs = {key: (None if value == "" else value) for key, value in values.items()}
        is_new = object_id in (None, "", "0")
        req = ObjectRequest(ctx, self.type, object_id=None if is_new else object_id, inputs=inputs)
        locking = self._lock_needed(ctx)
        if locking:
            self.locks.lock(self.type, req.object_id)
        try:
            return self._set(req, is_new, locking)
        finally:
            if locking:
                self.locks.unlock(self.type, None if is_new else object_id)
                if is_new and req.object_id:
                    self.locks.unlock(self.type, req.object_id)

    def delete(self, ctx: RequestContext, object_id: str) -> bool:
        """Delete an object (it stays locked, so its deletion is never committed back)."""
        if self._lock_needed(ctx):
            self.locks.lock(self.type, object_id)
        return bool(self.object.delete(ctx, object_id))

    # ====================================================================#
    # Lists, Primary Keys & Files
    # ====================================================================#

    def objects_list(self, ctx: RequestContext, list_filter: str | None, params: Mapping[str, Any]) -> dict[str, Any]:
        """List objects (``meta`` is always present)."""
        result = dict(self.object.objects_list(ctx, list_filter or None, params))
        result.setdefault("meta", {"current": 0, "total": 0})
        return result

    def identify(self, ctx: RequestContext, keys: Mapping[str, str]) -> str | None:
        """Identify an object by primary keys."""
        return self.object.get_by_primary(ctx, keys)

    def is_filtered(self, ctx: RequestContext, object_id: str, obj: Any) -> bool:
        """Check if an extension hides an object."""
        for extension in self.extensions:
            try:
                if extension.is_filtered(ctx, self.type, object_id, obj):
                    return True
            except Exception as error:
                ctx.logger.exception(error)
        return False

    # ====================================================================#
    # Private Methods
    # ====================================================================#

    def _set(self, req: ObjectRequest, is_new: bool, locking: bool) -> str | None:
        """Write algorithm (mirror of Php-Core ``IntelParserTrait::set()``)."""
        ownership = self.build(req)
        owners = {key: self._owner_of(ownership, key) for key in req.inputs}
        unknown = [key for key, owner in owners.items() if owner is None]
        self._notify("before_set", req)
        new_id: str | None = None
        failed: list[str] = []
        processed: builtins.set[str] = set()
        if is_new:
            self._write(req, ownership, owners, Phase.CREATE, processed, failed)
            req.object = self.object.create(req)
            if req.object is None:
                req.logger.error(f"{self.type}: unable to create object.")
                return self._done(req, None)
            new_id = self.object.object_id(req)
            req.object_id = new_id
            if locking and new_id:
                self.locks.lock(self.type, new_id)
            self._write(req, ownership, owners, Phase.POST_CREATE, processed, failed)
        else:
            req.object = self.object.load(req, str(req.object_id))
            if req.object is None:
                req.logger.error(f"{self.type}: unable to load object {req.object_id}.")
                return self._done(req, None)
            self._write(req, ownership, owners, Phase.UPDATE, processed, failed)
        leftovers = [key for key in owners if key not in processed and key not in unknown]
        for key in [*unknown, *leftovers, *failed]:
            req.logger.error(f"{self.type}: unable to write field => {key}")
        if unknown or leftovers or failed:
            return self._done(req, new_id)
        updated = self.object.update(req, req.is_to_update())
        return self._done(req, str(updated) if updated else new_id)

    def _write(
        self,
        req: ObjectRequest,
        ownership: Ownership,
        owners: Mapping[str, FieldsGroup | None],
        phase: str,
        processed: builtins.set[str],
        failed: list[str],
    ) -> None:
        """Run the groups of one phase, in pipeline order, on the values they own."""
        for group in self.pipeline:
            if phase not in group.phases:
                continue
            for key, owner in owners.items():
                if owner is not group:
                    continue
                value = req.inputs[key]
                if key in ownership.lists_owner:
                    value = _items(value)
                try:
                    result = group.set(req, key, value)
                except Exception as error:
                    req.logger.exception(error)
                    result = False
                processed.add(key)
                if result is False and key not in failed:
                    failed.append(key)

    def _done(self, req: ObjectRequest, object_id: str | None) -> str | None:
        """Notify extensions of the end of a write."""
        self._notify("after_set", req, object_id)
        return object_id

    def _notify(self, event: str, req: ObjectRequest, *args: Any) -> None:
        """Call an event on every extension, never failing the request."""
        for extension in self.extensions:
            try:
                getattr(extension, event)(req, *args)
            except Exception as error:
                req.logger.exception(error)

    @staticmethod
    def _owner_of(ownership: Ownership, key: str) -> FieldsGroup | None:
        """Group owning a field id or a list name."""
        return ownership.fields_owner.get(key) or ownership.lists_owner.get(key)

    @staticmethod
    def _lock_needed(ctx: RequestContext) -> bool:
        """Locks are skipped when the Splash server forces commits."""
        return ctx.remote_server.get("forcecommit") not in ("1", 1, True)


def _values(value: Any) -> list[Any]:
    """Values of a list field, in order."""
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _items(value: Any) -> list[dict[str, Any]]:
    """Items of a list received from Splash (decoded mapping or list), each a dict."""
    return [dict(item) for item in _values(value) if isinstance(item, Mapping)]
