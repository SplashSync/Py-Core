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

r"""Execute the tasks list of a request (mirror of Php-Core ``Components\\Router``)."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from splashpy.core.context import RequestContext
from splashpy.server.routers.base import TaskRouter, empty_response


def _delay_ms(started: float) -> float:
    """Milliseconds elapsed since a ``perf_counter()`` value."""
    return round(1000 * (time.perf_counter() - started), 3)


class TaskRunner:
    """Run every task of a request through the router of its service."""

    def __init__(self, routers: Mapping[str, TaskRouter]) -> None:
        """Store routers, indexed by service name."""
        self._routers = dict(routers)

    def run(self, service: str, inputs: Mapping[str, Any], outputs: dict[str, Any], ctx: RequestContext) -> bool:
        """Execute all tasks, store responses in ``outputs`` and return True if all succeeded.

        Output keys: ``tasks`` (responses indexed as in the request) and ``tasksinfos``.
        """
        started = time.perf_counter()
        router = self._validate(service, inputs, ctx)
        if router is None:
            return False
        count = success = 0
        outputs["tasks"] = {}
        for index, task in inputs["tasks"].items():
            count += 1
            response = self._execute(router, task, ctx)
            if response["result"]:
                success += 1
            outputs["tasks"][index] = response
        delay = _delay_ms(started)
        outputs["tasksinfos"] = {
            "DelayMs": delay,
            "DelayStr": f"{delay:.2f}  ms",
            "Performed": count,
            "Ok": success,
        }

        return count == success

    def _execute(self, router: TaskRouter, task: Mapping[str, Any], ctx: RequestContext) -> dict[str, Any]:
        """Execute one task, never letting an exception escape."""
        started = time.perf_counter()
        try:
            response = router.execute(task, ctx)
        except Exception as error:
            ctx.logger.exception(error)
            response = empty_response(task)
        delay = _delay_ms(started)
        response["id"] = task.get("id")
        response["delayms"] = delay
        response["delaystr"] = f"{delay:.2f}  ms"

        return response

    def _validate(self, service: str, inputs: Mapping[str, Any], ctx: RequestContext) -> TaskRouter | None:
        """Check the tasks list and find the router of the service."""
        tasks = inputs.get("tasks")
        if not tasks or not isinstance(tasks, Mapping):
            ctx.logger.error("Unable to perform requested action, task list is empty.")
            return None
        ctx.logger.debug(f"Found {len(tasks)} tasks in request.")
        for index, task in tasks.items():
            if not isinstance(task, Mapping):
                ctx.logger.error(f"Unable to perform requested action. Task {index} is not an Array.")
                return None
        router = self._routers.get(service)
        if router is None:
            ctx.logger.error(f"Unable to perform requested tasks, given router doesn't exist ({service}).")

        return router
