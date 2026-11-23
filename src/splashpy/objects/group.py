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

"""Fields groups: the explicit, ordered building blocks of an object.

A group declares the fields it owns (``build``), reads them (``get``) and writes them
(``set``). Its position in the object pipeline is explicit: ``after`` / ``before``
dependencies, then ``priority``, then ``code``. Nothing depends on method names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, ClassVar, Final, TypeVar

if TYPE_CHECKING:
    from splashpy.fields import FieldsFactory
    from splashpy.objects.request import ObjectRequest


class Phase:
    """Moments of a ``Set`` where a group writes its fields."""

    CREATE: Final = "create"
    """Before the object is created: the object is None, values are kept for ``create()``."""

    POST_CREATE: Final = "post_create"
    """Right after the object was created (relations, lines, images...)."""

    UPDATE: Final = "update"
    """On an existing object."""

    DEFAULT: Final = (POST_CREATE, UPDATE)
    """Default: once the object exists, new or not."""

    ALL: Final = (CREATE, POST_CREATE, UPDATE)
    """Every phase."""


class FieldsGroup:
    """Base class of fields groups."""

    code: ClassVar[str] = ""
    """Unique code of the group within an object (default: the class name)."""

    priority: ClassVar[int] = 100
    """Ordering priority: the lower, the earlier (used after dependencies)."""

    after: ClassVar[tuple[str, ...]] = ()
    """Codes of the groups that must run before this one."""

    before: ClassVar[tuple[str, ...]] = ()
    """Codes of the groups that must run after this one."""

    phases: ClassVar[tuple[str, ...]] = Phase.DEFAULT
    """Phases of a ``Set`` where this group writes its fields."""

    origin: str = "core"
    """Who provides the group: ``core`` or an extension name (set by the pipeline)."""

    @classmethod
    def group_code(cls) -> str:
        """Get the group code."""
        return cls.code or cls.__name__

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare the fields owned by this group."""

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read one owned field of ``req.object``.

        For a list field (``field@list``), return the values of every item (list or mapping).
        """
        return None

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
        """Write one owned field (or a whole list, by its list name).

        Call ``req.need_update()`` when something changed. Return False when the write failed.
        """
        return None


GroupT = TypeVar("GroupT", bound=type[FieldsGroup])


def fields_group(
    code: str,
    *,
    priority: int = 100,
    after: tuple[str, ...] = (),
    before: tuple[str, ...] = (),
    phases: tuple[str, ...] = Phase.DEFAULT,
) -> Callable[[GroupT], GroupT]:
    """Declare a fields group code and position in one place."""

    def decorate(cls: GroupT) -> GroupT:
        cls.code = code
        cls.priority = priority
        cls.after = tuple(after)
        cls.before = tuple(before)
        cls.phases = tuple(phases)
        return cls

    return decorate
