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

r"""Objects service router (mirror of Php-Core ``Server\Router\Objects``)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol

from splashpy.core.context import RequestContext, php_truthy
from splashpy.dictionary import SplObjectMethods
from splashpy.server.routers.base import empty_response, task_params

if TYPE_CHECKING:
    from splashpy.objects.handler import ObjectHandler


class ObjectsSource(Protocol):
    """What the Objects router needs to know about the client."""

    def object_types(self) -> list[str]:
        """Get available object types."""
        ...

    def object_handler(self, object_type: str) -> ObjectHandler | None:
        """Get the handler of an available object type."""
        ...


class ObjectsRouter:
    """Execute Objects tasks."""

    def __init__(self, source: ObjectsSource) -> None:
        """Store the client objects source."""
        self._source = source

    def execute(self, task: Mapping[str, Any], ctx: RequestContext) -> dict[str, Any]:
        """Execute one Objects task."""
        name = task.get("name")
        ctx.logger.debug(f"Objects => {name} ({task.get('desc')})")
        response = empty_response(task)
        if name == SplObjectMethods.OBJECTS:
            response["data"] = self._source.object_types()
            return _checked(response)
        if name == SplObjectMethods.COMMIT:
            ctx.logger.warning(f"Objects - Requested task not found => {name}")
            return response
        if name not in SplObjectMethods.ALL:
            ctx.logger.error(f"Objects - Requested task not found => {name}")
            return _checked(response)
        params = task_params(task)
        handler = self._handler(params, ctx)
        if handler is None:
            return response
        if name in (SplObjectMethods.DESC, SplObjectMethods.FIELDS, SplObjectMethods.LIST):
            response["data"] = self._admin(str(name), handler, params, ctx)
        elif name == SplObjectMethods.IDENTIFY:
            keys = params.get("keys")
            response["data"] = handler.identify(ctx, dict(keys)) if isinstance(keys, Mapping) and keys else None
            response["result"] = True
            return response
        else:
            object_id = params.get("id")
            if not _valid_id(object_id, ctx):
                return response
            response["data"] = self._sync(str(name), handler, str(object_id), params.get("fields"), ctx)
        return _checked(response)

    # ====================================================================#
    # Private Methods
    # ====================================================================#

    def _handler(self, params: Mapping[str, Any], ctx: RequestContext) -> ObjectHandler | None:
        """Validate task parameters and get the object handler."""
        if not params:
            ctx.logger.error("Object Router - Missing Task Parameters... ")
            return None
        object_type = params.get("type")
        if not object_type or not isinstance(object_type, str):
            ctx.logger.error("Object Router - Missing Object Type... ")
            return None
        handler = self._source.object_handler(object_type)
        if handler is None:
            ctx.logger.error("Object Router - Object Type is Invalid... ")
        return handler

    @staticmethod
    def _admin(name: str, handler: ObjectHandler, params: Mapping[str, Any], ctx: RequestContext) -> Any:
        """Execute Description, Fields or ObjectsList."""
        if name == SplObjectMethods.DESC:
            return handler.describe(ctx)
        if name == SplObjectMethods.FIELDS:
            return handler.fields(ctx)
        list_filter = params.get("filters")
        list_params = params.get("params")
        return handler.objects_list(
            ctx,
            list_filter if isinstance(list_filter, str) else None,
            list_params if isinstance(list_params, Mapping) else {},
        )

    @staticmethod
    def _sync(name: str, handler: ObjectHandler, object_id: str, fields: Any, ctx: RequestContext) -> Any:
        """Execute Get, Set or Delete."""
        if name == SplObjectMethods.GET:
            field_ids = [str(value) for value in fields.values()] if isinstance(fields, Mapping) else []
            if not php_truthy(object_id) or not field_ids:
                ctx.logger.error("Object Router - Get requires an object id and a fields list.")
                return None
            return handler.get(ctx, object_id, field_ids)
        if name == SplObjectMethods.SET:
            if not isinstance(fields, Mapping) or not fields:
                ctx.logger.error("Object Router - Set requires a fields list.")
                return None
            return handler.set(ctx, object_id, fields)
        if not php_truthy(object_id):
            return False
        return handler.delete(ctx, object_id)


def _valid_id(object_id: Any, ctx: RequestContext) -> bool:
    """Check an object id (empty string is valid: it means create)."""
    if object_id is None:
        return ctx.logger.error("Object Router - Object Id is empty.")
    if not isinstance(object_id, (str, int)):
        return ctx.logger.error("Object Router - Object Id is invalid.")
    try:
        if float(object_id) < 0:
            return ctx.logger.error("Object Router - Object Id is negative.")
    except ValueError:
        pass
    return True


def _checked(response: dict[str, Any]) -> dict[str, Any]:
    """Set the result: true when data is not empty (PHP ``empty()``)."""
    response["result"] = php_truthy(response["data"])
    return response
