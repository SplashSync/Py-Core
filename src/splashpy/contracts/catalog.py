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


"""Contracts catalog: field templates and scopes compiled by Php-Scopes.

A catalog is loaded from three files (``index.json``, ``templates.json``, ``scopes.json``) and
fully checked: supported format, every file listed by the index and matching its SHA-256.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from splashpy.dictionary import SplContracts

FileReader = Callable[[str], "bytes | None"]
"""Reads one catalog file by name, None when missing."""


class ContractsError(ValueError):
    """A catalog is missing, invalid or inconsistent, or a contract is unknown."""


@dataclass(frozen=True)
class Catalog:
    """A loaded and checked catalog of field templates and scopes (read only)."""

    index: Mapping[str, Any]
    """Catalog index: format, version, commit, files checksums."""

    templates: Mapping[str, Mapping[str, Any]]
    """Field templates, by code."""

    scopes: Mapping[str, Mapping[str, Any]]
    """Scopes, by code."""

    origin: str
    """Where the catalog was loaded from (``embedded``, ``cache``...)."""

    # ====================================================================#
    # Identity
    # ====================================================================#

    @property
    def version(self) -> str:
        """Released version of the catalog."""
        return str(self.index.get("version", ""))

    @property
    def commit(self) -> str:
        """Commit the catalog was released from."""
        return str(self.index.get("commit", ""))

    @property
    def generated_at(self) -> datetime | None:
        """Generation date of the catalog, None when unknown."""
        try:
            return datetime.fromisoformat(str(self.index.get("generated_at")))
        except ValueError:
            return None

    def is_newer_than(self, other: Catalog) -> bool:
        """Check if this catalog is another release, generated after the other one."""
        if self.commit == other.commit or self.generated_at is None or other.generated_at is None:
            return False
        return self.generated_at > other.generated_at

    # ====================================================================#
    # Templates
    # ====================================================================#

    def template(self, code: str) -> Mapping[str, Any]:
        """Get a field template.

        :raises ContractsError: when the template is unknown.
        """
        template = self.templates.get(code)
        if template is None:
            raise ContractsError(f"Unknown field template: {code}")
        return template

    def template_config(self, code: str, lang: str | None = None) -> dict[str, Any]:
        """Field configuration of a template, with its name and description in a language.

        Mirror of Php-Core ``AbstractFieldTemplate::getConfiguration()``.
        """
        template = self.template(code)
        config = dict(template.get("config") or {})
        config["name"] = text(template.get("name"), lang)
        config["desc"] = text(template.get("desc"), lang)
        return config

    # ====================================================================#
    # Scopes
    # ====================================================================#

    def scope(self, code: str) -> Mapping[str, Any]:
        """Get a scope.

        :raises ContractsError: when the scope is unknown.
        """
        scope = self.scopes.get(code)
        if scope is None:
            raise ContractsError(f"Unknown scope: {code}")
        return scope

    def resolve(self, code: str, object_type: str) -> list[str]:
        """Scope codes applying to an object type: the scope, then its children, recursively.

        Children are kept only when they impact the object type (``*`` impacts any type).
        """
        resolved: list[str] = []
        pending = [code]
        while pending:
            current = pending.pop(0)
            scope = self.scope(current)
            if current in resolved or not _impacts(scope, object_type):
                continue
            resolved.append(current)
            pending.extend(str(child) for child in scope.get("children") or [])
        return resolved

    def constraints(self, code: str, object_type: str) -> dict[str, Mapping[str, Any]]:
        """Field constraints of a scope (and of its resolved children) for an object type, by label."""
        constraints: dict[str, Mapping[str, Any]] = {}
        for resolved in self.resolve(code, object_type):
            constraints.update(self.scope(resolved).get("constraints") or {})
        return constraints

    # ====================================================================#
    # Loading
    # ====================================================================#

    @staticmethod
    def load(read: FileReader, origin: str) -> Catalog:
        """Load and check a catalog.

        :raises ContractsError: when a file is missing, invalid, or does not match the index.
        """
        index = _document(read, SplContracts.INDEX, None)
        files = index.get("files")
        if not isinstance(files, Mapping):
            raise ContractsError(f"{origin}: the index lists no files.")
        documents: dict[str, Mapping[str, Any]] = {}
        for name in SplContracts.FILES:
            entry = files.get(name)
            if not isinstance(entry, Mapping) or not entry.get("sha256"):
                raise ContractsError(f"{origin}: {name} is not listed in the index.")
            documents[name] = _document(read, name, str(entry["sha256"]))
        templates = documents[SplContracts.TEMPLATES].get("templates")
        scopes = documents[SplContracts.SCOPES].get("scopes")
        if not isinstance(templates, Mapping) or not isinstance(scopes, Mapping):
            raise ContractsError(f"{origin}: templates or scopes are missing.")
        return Catalog(index, templates, scopes, origin)


def text(values: Any, lang: str | None = None) -> str:
    """Read a catalog text in a language, english when not translated."""
    if not isinstance(values, Mapping):
        return str(values or "")
    return str(values.get(lang or SplContracts.DEFAULT_LANG) or values.get(SplContracts.DEFAULT_LANG) or "")


# ====================================================================#
# Private Functions
# ====================================================================#


def _document(read: FileReader, name: str, sha256: str | None) -> Mapping[str, Any]:
    """Read, verify and decode one catalog document."""
    raw = read(name)
    if raw is None:
        raise ContractsError(f"{name} is missing.")
    if sha256 is not None and hashlib.sha256(raw).hexdigest() != sha256:
        raise ContractsError(f"{name} does not match its checksum.")
    try:
        document = json.loads(raw)
    except ValueError as error:
        raise ContractsError(f"{name} is not valid JSON: {error}") from error
    if not isinstance(document, Mapping):
        raise ContractsError(f"{name} is not a JSON object.")
    if document.get("format") != SplContracts.FORMAT:
        raise ContractsError(f"{name}: unsupported format {document.get('format')!r}.")
    return document


def _impacts(scope: Mapping[str, Any], object_type: str) -> bool:
    """Check if a scope impacts an object type."""
    types = scope.get("types") or []
    return "*" in types or object_type in types
