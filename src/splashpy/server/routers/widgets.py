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

r"""Widgets service router (mirror of Php-Core ``Server\Router\Widgets``)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol

from splashpy.core.context import RequestContext, php_truthy
from splashpy.dictionary import SplWidgetsMethods
from splashpy.server.routers.base import empty_response, task_params

if TYPE_CHECKING:
    from splashpy.widgets.base import BaseWidget


class WidgetsSource(Protocol):
    """What the Widgets router needs to know about the client."""

    def widget_types(self) -> list[str]:
        """Get available widget types."""
        ...

    def widget(self, widget_type: str) -> BaseWidget | None:
        """Get an available widget."""
        ...


class WidgetsRouter:
    """Execute Widgets tasks."""

    def __init__(self, source: WidgetsSource) -> None:
        """Store the client widgets source."""
        self._source = source

    def execute(self, task: Mapping[str, Any], ctx: RequestContext) -> dict[str, Any]:
        """Execute one Widgets task."""
        name = task.get("name")
        ctx.logger.debug(f"Widgets => {name}")
        response = empty_response(task)
        params = task_params(task)
        if name == SplWidgetsMethods.LIST:
            response["data"] = self._source.widget_types()
        elif name in (SplWidgetsMethods.DEFINITION, SplWidgetsMethods.GET):
            widget_type = params.get("type")
            widget = self._source.widget(widget_type) if isinstance(widget_type, str) else None
            if widget is None:
                ctx.logger.error(f"Widgets - Unknown widget type => {widget_type}")
            elif name == SplWidgetsMethods.DEFINITION:
                response["data"] = widget.describe(ctx)
            else:
                widget_params = params.get("params")
                response["data"] = widget.get(ctx, widget_params if isinstance(widget_params, Mapping) else {})
        else:
            ctx.logger.error(f"Widgets - Requested task was not found => {name} ({task.get('desc')})")
        response["result"] = php_truthy(response["data"])
        return response
