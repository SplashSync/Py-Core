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

"""Faker widgets, one module each."""

from __future__ import annotations

from splashpy.faker.widgets.charts import FakerCharts
from splashpy.faker.widgets.infos import FakerInfos
from splashpy.widgets import BaseWidget

WIDGETS: tuple[type[BaseWidget], ...] = (FakerInfos, FakerCharts)
"""Every faker widget."""

__all__ = ["WIDGETS", "FakerCharts", "FakerInfos"]
