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

"""Faker widget: text, notifications and table blocks."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from splashpy.core.context import RequestContext
from splashpy.widgets import BaseWidget, WidgetRender


class FakerInfos(BaseWidget):
    """Text, notifications and table blocks."""

    name = "Faker Infos"
    description = "Faker widget with text, notifications and table blocks"
    icon = "fa fa-info-circle"

    def render(self, ctx: RequestContext, params: Mapping[str, Any], output: WidgetRender) -> bool | None:
        """Fill the widget."""
        output.set_sub_title(self.description)
        output.blocks.add_text_block("This is a faker text block.")
        output.blocks.add_notifications_block({"success": "Success!", "info": "Information", "warning": "Warning"})
        output.blocks.add_table_block([["Name", "Value"], ["Alpha", "1"], ["Beta", "2"]])
        return True
