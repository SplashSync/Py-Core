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

"""Widget blocks factory (mirror of Php-Core ``BlocksFactory``), one instance per render."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

COMMON_OPTIONS: Final = {"Width": "col-xs-12 col-sm-12 col-md-12 col-lg-12", "AllowHtml": False}
"""Default options of every block."""

MORRIS_TYPES: Final = ("Bar", "Area", "Line")
"""Morris chart types."""


class BlocksFactory:
    """Build the blocks of one widget render."""

    def __init__(self) -> None:
        """Create an empty list of blocks."""
        self._blocks: list[dict[str, Any]] = []
        self._current: dict[str, Any] | None = None

    # ====================================================================#
    # Core
    # ====================================================================#

    def add_block(self, block_type: str, options: Mapping[str, Any] | None = None) -> BlocksFactory:
        """Start a new block (the previous one is committed)."""
        self._commit()
        self._current = {"type": block_type, "options": dict(options or COMMON_OPTIONS), "data": {}}
        return self

    def set_data(self, name: str, value: Any) -> BlocksFactory:
        """Set a data key of the current block."""
        if self._current is not None:
            self._current["data"][name] = value
        return self

    def set_option(self, name: str, value: Any) -> BlocksFactory:
        """Set an option of the current block."""
        if self._current is not None:
            self._current["options"][name] = value
        return self

    def render(self) -> list[dict[str, Any]]:
        """Get every block."""
        self._commit()
        return list(self._blocks)

    # ====================================================================#
    # Blocks
    # ====================================================================#

    def add_text_block(self, text: str, options: Mapping[str, Any] | None = None) -> BlocksFactory:
        """Add a text block."""
        return self.add_block("TextBlock", options).set_data("text", text)

    def add_notifications_block(
        self, contents: Mapping[str, str], options: Mapping[str, Any] | None = None
    ) -> BlocksFactory:
        """Add notifications: ``error``, ``warning``, ``info``, ``success`` messages."""
        self.add_block("NotificationsBlock", options)
        for level in ("error", "warning", "info", "success"):
            if level in contents:
                self.set_data(level, contents[level])
        return self

    def add_table_block(self, rows: list[list[Any]], options: Mapping[str, Any] | None = None) -> BlocksFactory:
        """Add a table block (first row: headers)."""
        return self.add_block("TableBlock", options).set_data("rows", rows)

    def add_spark_info_block(
        self, contents: Mapping[str, Any], options: Mapping[str, Any] | None = None
    ) -> BlocksFactory:
        """Add a spark info block: ``title``, ``fa_icon``, ``glyph_icon``, ``value``, ``chart``."""
        self.add_block("SparkInfoBlock", options)
        return self._extract(contents, ("title", "fa_icon", "glyph_icon", "value", "chart"))

    def add_morris_graph_block(
        self,
        dataset: Sequence[Mapping[str, Any]],
        chart_type: str = "Bar",
        chart_options: Mapping[str, Any] | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> BlocksFactory:
        """Add a Morris Bar, Area or Line chart: ``title``, ``xkey``, ``ykeys``, ``labels`` options."""
        if chart_type not in MORRIS_TYPES:
            self.add_notifications_block({"warning": "Wrong Morris Chart Block Type (ie: Bar, Area, Line)"})
        self.add_block(f"Morris{chart_type}Block", options).set_data("dataset", dataset)
        return self._extract(chart_options or {}, ("title", "xkey", "ykeys", "labels"))

    def add_morris_donut_block(
        self,
        dataset: Sequence[Mapping[str, Any]],
        chart_options: Mapping[str, Any] | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> BlocksFactory:
        """Add a Morris donut chart."""
        self.add_block("MorrisDonutBlock", options).set_data("dataset", dataset)
        return self._extract(chart_options or {}, ("title",))

    # ====================================================================#
    # Private Methods
    # ====================================================================#

    def _extract(self, contents: Mapping[str, Any], keys: tuple[str, ...]) -> BlocksFactory:
        """Copy existing keys into the current block data."""
        for key in keys:
            if key in contents:
                self.set_data(key, contents[key])
        return self

    def _commit(self) -> None:
        """Store the current block."""
        if self._current is not None:
            self._blocks.append(self._current)
            self._current = None
