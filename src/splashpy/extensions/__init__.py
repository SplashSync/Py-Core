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

"""Extensions: what an add-on can contribute to a client.

An extension contributes objects, fields groups for existing objects, filters,
configurators (fields & description overrides), widgets, client information and
event listeners. Extensions are enabled per client: explicitly, or by name in the
client configuration for installed (entry point) extensions. Nothing is enabled
implicitly.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, ClassVar

from splashpy.core.info import ClientInfo

if TYPE_CHECKING:
    from splashpy.core.context import RequestContext
    from splashpy.objects.base import BaseObject
    from splashpy.objects.events import CommitEvent
    from splashpy.objects.group import FieldsGroup
    from splashpy.objects.request import ObjectRequest
    from splashpy.widgets.base import BaseWidget


class Extension:
    """Base class of every extension. Every hook has a neutral default."""

    name: ClassVar[str] = ""
    """Unique extension name, used in configuration allowlists."""

    priority: ClassVar[int] = 0
    """Execution priority: the lower, the earlier (hooks, events)."""

    # ====================================================================#
    # Contributions
    # ====================================================================#

    def objects(self) -> Sequence[BaseObject | type[BaseObject]]:
        """Objects provided by this extension."""
        return ()

    def fields_groups(self) -> Mapping[str, Sequence[type[FieldsGroup]]]:
        """Fields groups added to existing objects, by object type."""
        return {}

    def widgets(self) -> Sequence[BaseWidget | type[BaseWidget]]:
        """Widgets provided by this extension."""
        return ()

    def client_info(self, info: ClientInfo) -> ClientInfo:
        """Complete or override client information. Default: unchanged."""
        return info

    # ====================================================================#
    # Filters & Configurators
    # ====================================================================#

    def is_filtered(self, ctx: RequestContext, object_type: str, object_id: str, obj: Any) -> bool:
        """Hide an object from Splash (reads and commits). ``obj`` is None for commits."""
        return False

    def configure_description(self, ctx: RequestContext, object_type: str, description: dict[str, Any]) -> None:
        """Override an object description (modify it in place)."""

    def configure_fields(self, ctx: RequestContext, object_type: str, fields: dict[str, dict[str, Any]]) -> None:
        """Override published fields definitions (modify or remove them in place)."""

    # ====================================================================#
    # Events
    # ====================================================================#

    def before_set(self, req: ObjectRequest) -> None:
        """Handle the start of an object write by Splash."""

    def after_set(self, req: ObjectRequest, object_id: str | None) -> None:
        """Handle the end of an object write by Splash (``object_id`` None on failure)."""

    def on_commit(self, ctx: RequestContext, event: CommitEvent) -> None:
        """Handle a local change committed to Splash (sent or skipped)."""


__all__ = ["Extension"]
