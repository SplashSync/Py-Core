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

"""Admin service router: client information, available objects & widgets, self test."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from splashpy.core.context import RequestContext
from splashpy.dictionary import SplAdminMethods
from splashpy.server.routers.base import empty_response


class AdminSource(Protocol):
    """What the Admin router needs to know about the client."""

    def object_types(self) -> list[str]:
        """Get available object types."""
        ...

    def widget_types(self) -> list[str]:
        """Get available widget types."""
        ...

    def informations(self, ctx: RequestContext) -> dict[str, Any]:
        """Get client information."""
        ...

    def self_test(self, ctx: RequestContext) -> bool:
        """Run the client self test."""
        ...


class AdminRouter:
    r"""Execute Admin tasks (mirror of Php-Core ``Server\\Router\\Admin``)."""

    def __init__(self, source: AdminSource) -> None:
        """Store the client information source."""
        self._source = source

    def execute(self, task: Mapping[str, Any], ctx: RequestContext) -> dict[str, Any]:
        """Execute one Admin task."""
        name = task.get("name")
        ctx.logger.debug(f"Admin => {name} ({task.get('desc')})")
        response = empty_response(task)
        if name == SplAdminMethods.OBJECTS:
            response["data"] = self._source.object_types()
            response["result"] = bool(response["data"])
        elif name == SplAdminMethods.WIDGETS:
            response["data"] = self._source.widget_types()
            response["result"] = bool(response["data"])
        elif name == SplAdminMethods.SELF_TEST:
            response["result"] = self._source.self_test(ctx)
            response["data"] = response["result"]
        elif name == SplAdminMethods.INFOS:
            response["data"] = self._source.informations(ctx)
            response["result"] = bool(response["data"])
        else:
            ctx.logger.error(f"Admin - Requested task not found => {name}")

        return response
