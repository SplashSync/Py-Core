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

"""One field definition, published exactly like Php-Core ``AbstractField::toArray()``."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from typing import Any, Callable, Final

from splashpy.dictionary import SplFormats
from splashpy.fields.helpers import Inline, Lists
from splashpy.fields.types import FieldConstraints, FieldType, SyncMode

_VALID_ID: Final = re.compile(r"^[A-Za-z0-9_@\-]+$")
"""Allowed characters of field identifiers."""

_TAG: Final = re.compile(r"^[a-f0-9]{32}$")
"""Format of a metadata tag (md5)."""


def clean(text: str | None) -> str | None:
    """Trim a text, None when empty (Php-Core ``StringConverter::toUtf8()``)."""
    trimmed = (text or "").strip()
    return trimmed or None


def to_tag(item_type: str, item_prop: str) -> str:
    """Build the metadata tag of a microdata pair."""
    return hashlib.md5(f"{item_prop}{SplFormats.ID_SPLIT}{item_type}".encode(), usedforsecurity=False).hexdigest()


class ObjectField:
    """A field definition. Setters mirror Php-Core rules; errors are collected in ``errors``."""

    # ====================================================================#
    # Constructor
    # ====================================================================#

    def __init__(self, field_type: str, field_id: str | None = None) -> None:
        """Create a field of a type, with an optional identifier."""
        self.type = field_type
        self.id = field_id or ""
        self.errors: list[str] = []
        self._name: str | None = None
        self.desc: str | None = None
        self.group: str | None = None
        self.required = False
        self.read = True
        self.write = True
        self.index = False
        self.listed = False
        self.list_hidden = False
        self.logged = False
        self.primary = False
        self.sync_mode: str = SyncMode.BOTH
        self.item_type: str | None = None
        self.item_prop: str | None = None
        self.tag: str | None = None
        self.choices: list[dict[str, str]] = []
        self.associations: list[str] = []
        self.options: dict[str, Any] = {}
        self.not_tested = False

    # ====================================================================#
    # Core
    # ====================================================================#

    @property
    def name(self) -> str:
        """Field name, the identifier when not set."""
        return self._name or self.id

    def set_name(self, name: str) -> ObjectField:
        """Set the name; it is also the description when none is set."""
        self._name = clean(name)
        if not self.desc:
            self.desc = self._name
        return self

    def set_desc(self, desc: str) -> ObjectField:
        """Set the description."""
        self.desc = clean(desc)
        return self

    def set_group(self, group: str) -> ObjectField:
        """Set the group."""
        self.group = clean(group)
        return self

    @property
    def list_name(self) -> str | None:
        """List of a list field."""
        return Lists.list_name(self.id)

    @property
    def base_type(self) -> str:
        """Type of the values (the inner type for list fields)."""
        return Lists.field_name(self.type) or self.type

    def set_in_list(self, list_name: str) -> ObjectField:
        """Move the field into a list: ``id@list`` of type ``type@list``."""
        if not list_name:
            return self
        field_id = Lists.field_name(self.id) or self.id
        self.id = Lists.encode(list_name, field_id) or self.id
        self.type = Lists.encode(FieldType.LIST, self.base_type) or self.type
        return self

    # ====================================================================#
    # Synchronization
    # ====================================================================#

    def set_access(self, read: bool, write: bool) -> ObjectField:
        """Set read & write access."""
        self.read, self.write = read, write
        return self

    def set_primary(self, primary: bool) -> ObjectField:
        """Flag as primary key, refused for types that cannot be primary."""
        if primary and self.base_type not in FieldType.PRIMARY:
            self.errors.append(f"Primary flag is not allowed for type {self.base_type}")
            return self
        self.primary = primary
        return self

    def set_sync_mode(self, mode: str) -> ObjectField:
        """Set the preferred synchronization direction."""
        if mode not in SyncMode.ALL:
            self.errors.append(f"Invalid Sync Mode for Field {self.name}")
        else:
            self.sync_mode = mode
        return self

    # ====================================================================#
    # Metadata
    # ====================================================================#

    def set_micro_data(self, item_type: str, item_prop: str) -> ObjectField:
        """Set microdata; an empty part keeps the current one; both empty clears."""
        if not item_type and not item_prop:
            self.item_type = self.item_prop = self.tag = None
            return self
        item_prop = item_prop or self.item_prop or ""
        item_type = item_type or self.item_type or ""
        if item_type and item_prop:
            self.item_type, self.item_prop = item_type, item_prop
            self.tag = to_tag(item_type, item_prop)
        return self

    def alternate_tags(self) -> list[str]:
        """Get alternate metadata tags."""
        raw = self.options.get(FieldConstraints.ALT_TAGS)
        return self._filter_tags(Inline.to_list(raw) if isinstance(raw, str) else [])

    def set_alternate_tags(self, tags: list[str]) -> ObjectField:
        """Set alternate metadata tags (invalid ones and the own tag are ignored)."""
        filtered = self._filter_tags(tags)
        if not filtered:
            self.options.pop(FieldConstraints.ALT_TAGS, None)
            return self
        return self.add_option(FieldConstraints.ALT_TAGS, Inline.from_list(filtered))

    def add_alternate_micro_data(self, item_type: str, item_prop: str) -> ObjectField:
        """Add an alternate microdata pair."""
        if not item_type or not item_prop:
            return self
        return self.set_alternate_tags([*self.alternate_tags(), to_tag(item_type, item_prop)])

    # ====================================================================#
    # Options & Choices
    # ====================================================================#

    def set_multi_lang(self, iso_code: str, is_default: bool) -> ObjectField:
        """Mark as translated: non default languages get an ``_iso`` suffix."""
        if not self.is_valid_iso_code(iso_code) or self.base_type not in FieldType.MULTI_LANG:
            return self
        self.add_option(FieldConstraints.LANGUAGE, iso_code)
        if not is_default:
            self.id = f"{self.id}_{iso_code}"
            if self.item_type and self.item_prop:
                self.set_micro_data(f"{self.item_type}/{iso_code}", self.item_prop)
        return self

    def add_choice(self, value: str, description: str) -> ObjectField:
        """Add a possible value."""
        self.choices.append({"key": str(value), "value": clean(description) or ""})
        return self

    def add_option(self, key: str, value: Any = True) -> ObjectField:
        """Add an option."""
        if not key:
            self.errors.append("Field Option Type Cannot be Empty")
        else:
            self.options[key] = value
        return self

    def set_associations(self, field_ids: list[str]) -> ObjectField:
        """Set associated fields (tested together), duplicates removed."""
        self.associations = list(dict.fromkeys(field_ids))
        return self

    # ====================================================================#
    # Bulk Update
    # ====================================================================#

    def update(self, values: Mapping[str, Any]) -> ObjectField:
        """Update the definition from raw properties (mirror of Php-Core ``AbstractField::update()``).

        Used to apply field templates: only valid values are applied, missing keys are kept.
        """
        _update_string(values, "type", lambda value: setattr(self, "type", value))
        _update_string(values, "name", self.set_name)
        _update_string(values, "desc", self.set_desc)
        _update_string(values, "group", self.set_group)
        _update_bool(values, "required", lambda value: setattr(self, "required", value))
        _update_bool(values, "read", lambda value: setattr(self, "read", value))
        _update_bool(values, "write", lambda value: setattr(self, "write", value))
        _update_bool(values, "index", lambda value: setattr(self, "index", value))
        _update_bool(values, "primary", self.set_primary)
        _update_bool(values, "log", lambda value: setattr(self, "logged", value))
        _update_string(values, "syncmode", self.set_sync_mode)
        _update_bool(values, "inlist", lambda value: setattr(self, "listed", value))
        _update_bool(values, "hlist", lambda value: setattr(self, "list_hidden", value))
        self._update_metadata(values)
        self._update_options(values)
        self._update_choices(values)
        self._update_tests(values)
        return self

    # ====================================================================#
    # Validation & Export
    # ====================================================================#

    def is_valid(self) -> bool:
        """Check the definition is complete (Php-Core ``isValid()``)."""
        if not self.type:
            self.errors.append("Field type is missing")
            return False
        if not self.id:
            self.errors.append("Field identifier is missing")
            return False
        if not _VALID_ID.match(self.id):
            self.errors.append(f"Field identifier is invalid: {self.id}")
            return False
        if not self.desc:
            self.errors.append(f"Field description is missing: {self.id}")
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """Export the definition, keys in Php-Core order."""
        return {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "desc": self.desc,
            "group": self.group,
            "required": self.required,
            "read": self.read,
            "write": self.write,
            "index": self.index,
            "inlist": self.listed,
            "hlist": self.list_hidden,
            "log": self.logged,
            "primary": self.primary,
            "syncmode": self.sync_mode,
            "itemtype": self.item_type,
            "itemprop": self.item_prop,
            "tag": self.tag,
            "choices": [dict(choice) for choice in self.choices],
            "asso": list(self.associations),
            "options": dict(self.options),
            "notest": self.not_tested,
        }

    @staticmethod
    def is_valid_iso_code(iso_code: str | None) -> bool:
        """Check a language code length (2 to 5 characters)."""
        return 2 <= len(iso_code or "") <= 5

    def _update_metadata(self, values: Mapping[str, Any]) -> None:
        """Update microdata (then the tag, only when none is set)."""
        item_type = values.get("itemtype", self.item_type)
        item_prop = values.get("itemprop", self.item_prop)
        valid = _is_scalar_or_none(item_type) and _is_scalar_or_none(item_prop)
        if valid and (item_type != self.item_type or item_prop != self.item_prop):
            self.set_micro_data(_php_string(item_type), _php_string(item_prop))
        if not self.tag and "tag" in values:
            _update_string(values, "tag", lambda value: setattr(self, "tag", value))

    def _update_options(self, values: Mapping[str, Any]) -> None:
        """Add options with a non empty key and a truthy scalar value."""
        options = values.get("options")
        if isinstance(options, Mapping):
            for key, value in options.items():
                if key and value and isinstance(key, str) and _is_scalar(value):
                    self.add_option(key, value)

    def _update_choices(self, values: Mapping[str, Any]) -> None:
        """Replace choices: ``{value: label}`` or ``[{key, value}]`` items."""
        choices = values.get("choices")
        if not isinstance(choices, (Mapping, list)):
            return
        self.choices = []
        items = choices.items() if isinstance(choices, Mapping) else enumerate(choices)
        for key, choice in items:
            if key and choice and isinstance(key, str) and isinstance(choice, str):
                self.add_choice(key, choice)
            if isinstance(choice, Mapping):
                struct_key, struct_value = choice.get("key"), choice.get("value")
                if struct_key and struct_value and isinstance(struct_key, str) and isinstance(struct_value, str):
                    self.add_choice(struct_key, struct_value)

    def _update_tests(self, values: Mapping[str, Any]) -> None:
        """Replace associations, update the not tested flag."""
        associations = values.get("asso")
        if isinstance(associations, (list, tuple)):
            self.set_associations([value for value in associations if value and isinstance(value, str)])
        _update_bool(values, "notest", lambda value: setattr(self, "not_tested", value))

    def _filter_tags(self, tags: list[Any]) -> list[str]:
        """Keep valid, unique tags, different from the own tag."""
        unique: dict[str, None] = {}
        for tag in tags:
            if isinstance(tag, str) and _TAG.match(tag) and tag != self.tag:
                unique[tag] = None
        return list(unique)


def _update_string(values: Mapping[str, Any], key: str, setter: Callable[[str], Any]) -> None:
    """Apply a non empty string value (Php-Core ``updateStringValue``)."""
    value = values.get(key)
    if value and isinstance(value, str):
        setter(value)


def _update_bool(values: Mapping[str, Any], key: str, setter: Callable[[bool], Any]) -> None:
    """Apply a scalar value as a boolean (Php-Core ``updateBooleanValue``)."""
    value = values.get(key)
    if value is not None and _is_scalar(value):
        setter(_php_bool(value))


def _is_scalar(value: Any) -> bool:
    """PHP ``is_scalar()``."""
    return isinstance(value, (str, int, float, bool))


def _is_scalar_or_none(value: Any) -> bool:
    """PHP ``is_null() || is_scalar()``."""
    return value is None or _is_scalar(value)


def _php_string(value: Any) -> str:
    """PHP ``(string)`` cast of a scalar or null."""
    if value is None or value is False:
        return ""
    return "1" if value is True else str(value)


def _php_bool(value: Any) -> bool:
    """PHP ``(bool)`` cast of a scalar."""
    return value not in ("", "0", 0, 0.0, False)
