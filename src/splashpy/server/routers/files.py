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

r"""Files service router (mirror of Php-Core ``Server\Router\Files``).

Files are served by objects (``BaseObject.read_file``), identified by path and md5.
As in Php-Core 3.0, ``SetFile`` and ``DeleteFile`` are not routed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from splashpy.core.context import RequestContext, php_truthy
from splashpy.dictionary import SplFilesMethods
from splashpy.server.routers.base import empty_response, task_params


class FilesSource(Protocol):
    """What the Files router needs to know about the client."""

    def read_file(self, ctx: RequestContext, path: str, md5: str) -> dict[str, Any] | None:
        """Read a file published by an object."""
        ...


class FilesRouter:
    """Execute Files tasks."""

    def __init__(self, source: FilesSource) -> None:
        """Store the client files source."""
        self._source = source

    def execute(self, task: Mapping[str, Any], ctx: RequestContext) -> dict[str, Any]:
        """Execute one Files task."""
        name = task.get("name")
        response = empty_response(task)
        params = task_params(task)
        path = params.get("path") or params.get("file")
        md5 = params.get("md5")
        if not path or not md5 or not isinstance(path, str) or not isinstance(md5, str):
            ctx.logger.error("File - Missing path or md5 parameters.")
            return response
        if name == SplFilesMethods.EXISTS:
            response["data"] = self._source.read_file(ctx, path, md5) is not None
        elif name == SplFilesMethods.GET:
            response["data"] = self._source.read_file(ctx, path, md5)
        else:
            ctx.logger.error(f"File - Requested task not found => {name}")
        response["result"] = php_truthy(response["data"])
        return response
