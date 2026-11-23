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

"""Widgets: information blocks shown in Splash.

Every call renders a NEW :class:`WidgetRender`: nothing is shared between widgets,
calls or threads (1.0 widgets shared one class-level output).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar, Final

from splashpy.core.context import RequestContext
from splashpy.fields import FieldsFactory
from splashpy.widgets.blocks import BlocksFactory


class WidgetSize:
    """Bootstrap widths of widgets."""

    XS: Final = "col-sm-6 col-md-4 col-lg-3"
    SM: Final = "col-sm-6 col-md-6 col-lg-4"
    DEFAULT: Final = "col-sm-12 col-md-6 col-lg-6"
    M: Final = "col-sm-12 col-md-6 col-lg-6"
    L: Final = "col-sm-12 col-md-6 col-lg-8"
    XL: Final = "col-sm-12 col-md-12 col-lg-12"


class WidgetRender:
    """Output of one widget call: title, subtitle, icon and blocks."""

    def __init__(self) -> None:
        """Create an empty render, with its own blocks factory."""
        self.blocks = BlocksFactory()
        self._out: dict[str, Any] = {}

    def set_title(self, text: str) -> WidgetRender:
        """Set the title."""
        self._out["title"] = text
        return self

    def set_sub_title(self, text: str) -> WidgetRender:
        """Set the subtitle."""
        self._out["subtitle"] = text
        return self

    def set_icon(self, icon: str) -> WidgetRender:
        """Set the icon."""
        self._out["icon"] = icon
        return self

    def to_dict(self) -> dict[str, Any]:
        """Export the render (only the keys that were set, plus blocks)."""
        out = dict(self._out)
        blocks = self.blocks.render()
        if blocks:
            out["blocks"] = blocks
        return out


class BaseWidget:
    """A Splash widget: declare its identity, then implement :meth:`render`."""

    type: ClassVar[str] = ""
    """Widget type (default: the class name)."""

    name: ClassVar[str] = ""
    """Display name (default: the type)."""

    description: ClassVar[str] = ""
    """Description (default: the name)."""

    icon: ClassVar[str] = "fa fa-info"
    """Font Awesome icon."""

    disabled: ClassVar[bool] = False
    """Disabled widgets are not exposed."""

    options: ClassVar[Mapping[str, Any]] = {"Width": WidgetSize.DEFAULT}
    """Default display options."""

    @classmethod
    def widget_type(cls) -> str:
        """Get the widget type."""
        return cls.type or cls.__name__

    def build_parameters(self, factory: FieldsFactory, ctx: RequestContext) -> None:
        """Declare widget parameters as fields (none by default)."""

    def describe(self, ctx: RequestContext) -> dict[str, Any]:
        """Widget description."""
        name = self.name or self.widget_type()
        factory = FieldsFactory()
        self.build_parameters(factory, ctx)
        return {
            "type": self.widget_type(),
            "name": name,
            "description": self.description or name,
            "icon": self.icon,
            "disabled": self.disabled,
            "options": dict(self.options),
            "parameters": factory.publish() if factory.current() or factory.fields() else {},
        }

    def get(self, ctx: RequestContext, params: Mapping[str, Any]) -> dict[str, Any] | None:
        """Render the widget: title and icon by default, then :meth:`render`."""
        output = WidgetRender().set_title(self.name or self.widget_type()).set_icon(self.icon)
        if self.render(ctx, params, output) is False:
            return None
        return output.to_dict()

    def render(self, ctx: RequestContext, params: Mapping[str, Any], output: WidgetRender) -> bool | None:
        """Fill the render (``output.blocks`` for contents). Return False on failure."""
        raise NotImplementedError
