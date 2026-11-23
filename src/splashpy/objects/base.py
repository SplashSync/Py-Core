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

"""Base class of Splash objects: what a connector implements for each object type."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from splashpy.core.context import RequestContext
from splashpy.objects.group import FieldsGroup
from splashpy.objects.request import ObjectRequest


class BaseObject:
    """A Splash object type.

    Declare its identity and its ``groups`` (fields groups classes), then implement
    ``load``, ``create``, ``update``, ``delete``, ``object_id`` and ``objects_list``.
    Implement ``get_by_primary`` to support primary keys identification.
    """

    # ====================================================================#
    # Identity
    # ====================================================================#

    type: ClassVar[str] = ""
    """Splash object type (default: the class name)."""

    name: ClassVar[str] = ""
    """Display name (default: the type)."""

    description: ClassVar[str] = ""
    """Description (default: the name)."""

    icon: ClassVar[str] = "fa fa-cubes"
    """Font Awesome icon."""

    disabled: ClassVar[bool] = False
    """Disabled objects are not exposed."""

    priority: ClassVar[int] = 100
    """Order of declaration to Splash; an extension object replaces a type of lower priority."""

    # ====================================================================#
    # Synchronization Rules
    # ====================================================================#

    allow_push_created: ClassVar[bool] = True
    allow_push_updated: ClassVar[bool] = True
    allow_push_deleted: ClassVar[bool] = True
    enable_push_created: ClassVar[bool] = True
    enable_push_updated: ClassVar[bool] = True
    enable_push_deleted: ClassVar[bool] = True
    enable_pull_created: ClassVar[bool] = True
    enable_pull_updated: ClassVar[bool] = True
    enable_pull_deleted: ClassVar[bool] = True

    # ====================================================================#
    # Fields Groups
    # ====================================================================#

    groups: ClassVar[Sequence[builtins.type[FieldsGroup]]] = ()
    """Fields groups of the object (their order here does not matter)."""

    @classmethod
    def object_type(cls) -> str:
        """Get the Splash object type."""
        return cls.type or cls.__name__

    def describe(self) -> dict[str, Any]:
        """Object description, keys in Php-Core order."""
        name = self.name or self.object_type()
        return {
            "type": self.object_type(),
            "name": name,
            "description": self.description or name,
            "icon": self.icon,
            "disabled": self.disabled,
            "allow_push_created": self.allow_push_created,
            "allow_push_updated": self.allow_push_updated,
            "allow_push_deleted": self.allow_push_deleted,
            "enable_push_created": self.enable_push_created,
            "enable_push_updated": self.enable_push_updated,
            "enable_push_deleted": self.enable_push_deleted,
            "enable_pull_created": self.enable_pull_created,
            "enable_pull_updated": self.enable_pull_updated,
            "enable_pull_deleted": self.enable_pull_deleted,
        }

    # ====================================================================#
    # To Implement
    # ====================================================================#

    def load(self, req: ObjectRequest, object_id: str) -> Any:
        """Load a native object, None when not found."""
        raise NotImplementedError

    def create(self, req: ObjectRequest) -> Any:
        """Create a native object (and persist it, so its id exists), None on failure.

        Values received are in ``req.inputs``; ``Phase.CREATE`` groups may have stored more in ``req.stash``.
        """
        raise NotImplementedError

    def object_id(self, req: ObjectRequest) -> str | None:
        """Get the identifier of ``req.object``."""
        raise NotImplementedError

    def update(self, req: ObjectRequest, needed: bool) -> str | None:
        """Save ``req.object`` if ``needed``, and return its identifier (None on failure)."""
        raise NotImplementedError

    def delete(self, ctx: RequestContext, object_id: str) -> bool:
        """Delete an object; deleting a missing object is a success."""
        raise NotImplementedError

    def objects_list(self, ctx: RequestContext, filter: str | None, params: Mapping[str, Any]) -> dict[str, Any]:
        """List objects. Build the result with :meth:`list_result`.

        :param params: ``max``, ``offset``, ``sortfield``, ``sortorder`` (decoded strings).
        """
        raise NotImplementedError

    def get_by_primary(self, ctx: RequestContext, keys: Mapping[str, str]) -> str | None:
        """Identify an object by its primary fields: its id when exactly one object matches."""
        return None

    def read_file(self, ctx: RequestContext, path: str, md5: str) -> dict[str, Any] | None:
        """Read a file published by this object (see ``Files.read``), None when not found."""
        return None

    # ====================================================================#
    # Helpers
    # ====================================================================#

    @staticmethod
    def list_result(items: Sequence[Mapping[str, Any]], total: int) -> dict[str, Any]:
        """Build an objects list result: items plus ``meta`` (``current``, ``total``)."""
        result: dict[str, Any] = {str(index): dict(item) for index, item in enumerate(items)}
        result["meta"] = {"current": len(items), "total": total}
        return result

    @staticmethod
    def list_params(params: Mapping[str, Any], default_max: int = 25) -> tuple[int, int]:
        """Read ``max`` and ``offset`` list parameters."""

        def read(key: str, default: int) -> int:
            try:
                return max(int(params.get(key) or default), 0)
            except (TypeError, ValueError):
                return default

        return read("max", default_max), read("offset", 0)
