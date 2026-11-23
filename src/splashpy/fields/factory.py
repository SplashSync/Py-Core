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

"""Fluent fields factory, published exactly like Php-Core ``FieldsFactory``.

A factory is an instance, created for one build: nothing is shared between objects,
requests or threads.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from splashpy.fields.field import ObjectField, clean
from splashpy.fields.types import SyncMode


class FieldsFactory:
    """Build field definitions with chained calls, then publish them."""

    # ====================================================================#
    # Constructor
    # ====================================================================#

    def __init__(self) -> None:
        """Create an empty factory."""
        self._fields: dict[str, ObjectField] = {}
        self._current: ObjectField | None = None
        self._default_language: str | None = None
        self.errors: list[str] = []

    # ====================================================================#
    # Fields Creation
    # ====================================================================#

    def create(self, field_type: str, field_id: str | None = None, field_name: str | None = None) -> FieldsFactory:
        """Start a new field (the previous one is committed)."""
        self._commit()
        self._current = ObjectField(field_type, field_id)
        if field_name:
            self._current.set_name(field_name)
        return self

    def identifier(self, field_id: str) -> FieldsFactory:
        """Set the identifier."""
        return self._apply(lambda field: setattr(field, "id", field_id))

    def name(self, field_name: str) -> FieldsFactory:
        """Set the name (also the description when none is set)."""
        return self._apply(lambda field: field.set_name(field_name))

    def description(self, field_desc: str) -> FieldsFactory:
        """Set the description."""
        return self._apply(lambda field: field.set_desc(field_desc))

    def group(self, field_group: str) -> FieldsFactory:
        """Set the group."""
        return self._apply(lambda field: field.set_group(field_group))

    def in_list(self, list_name: str) -> FieldsFactory:
        """Move the field into a list: ``field@list``."""
        return self._apply(lambda field: field.set_in_list(list_name))

    # ====================================================================#
    # Flags
    # ====================================================================#

    def is_required(self, required: bool = True) -> FieldsFactory:
        """Flag as required."""
        return self._apply(lambda field: setattr(field, "required", bool(required)))

    def is_primary(self, primary: bool = True) -> FieldsFactory:
        """Flag as primary key (only for primary capable types)."""
        return self._apply(lambda field: field.set_primary(bool(primary)))

    def is_indexed(self, indexed: bool = True) -> FieldsFactory:
        """Flag as indexed."""
        return self._apply(lambda field: setattr(field, "index", bool(indexed)))

    def is_read_only(self, read_only: bool = True) -> FieldsFactory:
        """Flag as read only (False changes nothing)."""
        if read_only:
            self._apply(lambda field: field.set_access(read=True, write=False))
        return self

    def is_write_only(self, write_only: bool = True) -> FieldsFactory:
        """Flag as write only (False changes nothing)."""
        if write_only:
            self._apply(lambda field: field.set_access(read=False, write=True))
        return self

    def is_listed(self, listed: bool = True) -> FieldsFactory:
        """Show in objects lists."""
        return self._apply(lambda field: setattr(field, "listed", bool(listed)))

    def is_list_hidden(self, hidden: bool = True) -> FieldsFactory:
        """Return in objects lists, but hidden."""
        return self._apply(lambda field: setattr(field, "list_hidden", bool(hidden)))

    def is_logged(self, logged: bool = True) -> FieldsFactory:
        """Log changes of this field."""
        return self._apply(lambda field: setattr(field, "logged", bool(logged)))

    def is_not_tested(self, not_tested: bool = True) -> FieldsFactory:
        """Exclude from automated tests."""
        return self._apply(lambda field: setattr(field, "not_tested", bool(not_tested)))

    # ====================================================================#
    # Sync Modes
    # ====================================================================#

    def set_prefer_both(self) -> FieldsFactory:
        """Prefer both directions (default)."""
        return self._apply(lambda field: field.set_sync_mode(SyncMode.BOTH))

    def set_prefer_read(self) -> FieldsFactory:
        """Prefer reading (export) from this node."""
        return self._apply(lambda field: field.set_sync_mode(SyncMode.READ))

    def set_prefer_write(self) -> FieldsFactory:
        """Prefer writing (import) to this node."""
        return self._apply(lambda field: field.set_sync_mode(SyncMode.WRITE))

    def set_prefer_none(self) -> FieldsFactory:
        """No preferred direction."""
        return self._apply(lambda field: field.set_sync_mode(SyncMode.NONE))

    # ====================================================================#
    # Metadata
    # ====================================================================#

    def micro_data(self, item_type: str, item_prop: str) -> FieldsFactory:
        """Set microdata (schema.org type & property)."""
        return self._apply(lambda field: field.set_micro_data(item_type, item_prop))

    def alternate_micro_data(self, item_type: str, item_prop: str) -> FieldsFactory:
        """Add an alternate microdata pair."""
        return self._apply(lambda field: field.add_alternate_micro_data(item_type, item_prop))

    def alternate_tags(self, tags: list[str]) -> FieldsFactory:
        """Set alternate metadata tags."""
        return self._apply(lambda field: field.set_alternate_tags(tags))

    # ====================================================================#
    # Choices, Options & Associations
    # ====================================================================#

    def add_choices(self, choices: Mapping[str, str | None]) -> FieldsFactory:
        """Add possible values (``value: description``; empty description → capitalized value)."""
        for value, description in choices.items():
            self.add_choice(str(value), str(description or "") or str(value).capitalize())
        return self

    def add_choice(self, value: str, description: str) -> FieldsFactory:
        """Add a possible value."""
        return self._apply(lambda field: field.add_choice(value, clean(description) or ""))

    def add_options(self, options: Mapping[str, Any]) -> FieldsFactory:
        """Add options."""
        for key, value in options.items():
            self.add_option(key, value)
        return self

    def add_option(self, key: str, value: Any = True) -> FieldsFactory:
        """Add an option."""
        return self._apply(lambda field: field.add_option(key, value))

    def association(self, *field_ids: str) -> FieldsFactory:
        """Associate fields: they are tested together."""
        ids = [field_id for field_id in field_ids if isinstance(field_id, str)]
        return self._apply(lambda field: field.set_associations(ids))

    # ====================================================================#
    # Languages
    # ====================================================================#

    def set_default_language(self, iso_code: str | None) -> FieldsFactory:
        """Set the default language: its fields keep their identifier."""
        if ObjectField.is_valid_iso_code(iso_code):
            self._default_language = iso_code
        return self

    def is_default_language(self, iso_code: str | None) -> bool:
        """Check if a language is the default one."""
        return (iso_code or "").lower() == (self._default_language or "").lower()

    def set_multi_lang(self, iso_code: str) -> FieldsFactory:
        """Mark the field as a translation."""
        return self._apply(lambda field: field.set_multi_lang(iso_code, self.is_default_language(iso_code)))

    # ====================================================================#
    # Results
    # ====================================================================#

    def current(self) -> ObjectField | None:
        """Get the field being built."""
        return self._current

    def fields(self) -> dict[str, ObjectField]:
        """Get committed fields, by identifier (the current one is committed first)."""
        self._commit()
        return dict(self._fields)

    def publish(self) -> dict[str, dict[str, Any]]:
        """Export every valid field definition, indexed by identifier, then reset."""
        published = {field_id: field.to_dict() for field_id, field in self.fields().items()}
        if not published:
            self.errors.append("No fields were defined.")
        self._fields = {}
        self._default_language = None
        return published

    # ====================================================================#
    # Private Methods
    # ====================================================================#

    def _apply(self, action: Any) -> FieldsFactory:
        """Apply an action to the current field, if any."""
        if self._current is None:
            self.errors.append("No field is being built.")
        else:
            action(self._current)
        return self

    def _commit(self) -> None:
        """Store the current field if valid."""
        field = self._current
        if field is None:
            return
        if field.is_valid():
            self._fields[field.id] = field
        self.errors.extend(field.errors)
        self._current = None
