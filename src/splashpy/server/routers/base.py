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

"""Base of task routers: one router executes the tasks of one Splash service."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from splashpy.core.context import RequestContext


class TaskRouter(Protocol):
    """Execute one task of a Splash service."""

    def execute(self, task: Mapping[str, Any], ctx: RequestContext) -> dict[str, Any]:
        """Execute a task and return its response (see :func:`empty_response`)."""
        ...


def empty_response(task: Mapping[str, Any]) -> dict[str, Any]:
    """Build a failed task response (mirror of Php-Core ``Router::getEmptyResponse()``)."""
    return {
        "result": False,
        "data": None,
        "name": task.get("name", ""),
        "desc": task.get("desc", ""),
    }


def task_params(task: Mapping[str, Any]) -> Mapping[str, Any]:
    """Get the parameters of a task, an empty mapping when missing or invalid."""
    params = task.get("params")

    return params if isinstance(params, Mapping) else {}
