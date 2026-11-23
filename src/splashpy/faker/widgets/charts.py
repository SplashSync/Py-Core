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

"""Faker widget: spark info and Morris charts blocks."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

from splashpy.core.context import RequestContext
from splashpy.widgets import BaseWidget, WidgetRender, WidgetSize


class FakerCharts(BaseWidget):
    """Spark info and Morris charts blocks."""

    name = "Faker Charts"
    description = "Faker widget with charts"
    icon = "fa fa-chart-bar"
    options: ClassVar[Mapping[str, Any]] = {"Width": WidgetSize.XL}

    def render(self, ctx: RequestContext, params: Mapping[str, Any], output: WidgetRender) -> bool | None:
        """Fill the widget."""
        dataset = [{"label": f"Day {day}", "value": day * 3} for day in range(1, 8)]
        output.blocks.add_spark_info_block({"title": "Total", "fa_icon": "line-chart", "value": "84"})
        output.blocks.add_morris_graph_block(dataset, "Bar", {"xkey": "label", "ykeys": ["value"], "labels": ["Value"]})
        output.blocks.add_morris_donut_block(dataset[:3])
        return True
