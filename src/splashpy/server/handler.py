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

"""Server side of the Splash services (mirror of Php-Core ``SplashServer``).

Behaviours checked by the Toolkit validator are kept: a wrong webservice id or an
undecryptable message gives an EMPTY response (nil), never an error message.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from splashpy.core.context import RequestContext, php_truthy
from splashpy.core.info import server_info
from splashpy.dictionary import SplDefinition, SplServices
from splashpy.protocol import MessageCodec, MessageError
from splashpy.server.runner import TaskRunner


class ServiceHandler:
    """Serve one call of a Splash service, at message level."""

    def __init__(self, codec: MessageCodec, runner: TaskRunner) -> None:
        """Store the message codec and the tasks runner."""
        self._codec = codec
        self._runner = runner

    def handle(self, service: str, ws_id: str | None, data: str | None, ctx: RequestContext) -> str | None:
        """Serve a call and return the packed response, None for an empty response.

        :param service: called service (``Ping``, ``Connect``, ``Admin``...).
        :param ws_id: webservice id sent by the caller.
        :param data: packed message sent by the caller.
        """
        if service == SplServices.PING:
            return self._ping(ctx)
        if service == SplServices.CONNECT:
            return self._connect(ws_id, data, ctx)

        return self._run(service, ws_id, data, ctx)

    # ====================================================================#
    # Services
    # ====================================================================#

    def _ping(self, ctx: RequestContext) -> str:
        """Answer a ping: unsecured, no id check."""
        ctx.logger.info("Ping Successful.")

        return self._codec.pack({"result": True}, secured=False)

    def _connect(self, ws_id: str | None, data: str | None, ctx: RequestContext) -> str | None:
        """Answer a connection check."""
        if ws_id != ctx.config.ws_id:
            return None
        outputs = self._receive(data, ctx)
        if outputs is None:
            return None
        ctx.logger.info(f"Connection Requested ({SplDefinition.NAME} V{SplDefinition.VERSION})")

        return self._transmit(outputs, True, ctx)

    def _run(self, service: str, ws_id: str | None, data: str | None, ctx: RequestContext) -> str | None:
        """Execute the tasks of an Admin, Objects, Files or Widgets call."""
        if ws_id != ctx.config.ws_id:
            return None
        inputs: dict[str, Any] = {}
        outputs = self._receive(data, ctx, inputs)
        if outputs is None:
            return None
        try:
            result = self._runner.run(service, inputs, outputs, ctx)
        except Exception as error:
            ctx.logger.exception(error)
            result = False

        return self._transmit(outputs, result, ctx)

    # ====================================================================#
    # Private Methods
    # ====================================================================#

    def _receive(
        self, data: str | None, ctx: RequestContext, inputs: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Unpack a request, apply its flags and start the outputs. None when unreadable."""
        try:
            received = self._codec.unpack(data or "")
        except MessageError as error:
            ctx.logger.error(str(error))
            return None
        if inputs is not None:
            inputs.update(received)
        server = received.get("server")
        ctx.remote_server = dict(server) if isinstance(server, Mapping) else {}
        ctx.debug = php_truthy(received.get("debug"))
        if php_truthy(received.get("verbose")):
            ctx.logger.verbose = True

        return {"server": server_info(ctx)}

    def _transmit(self, outputs: dict[str, Any], result: bool, ctx: RequestContext) -> str:
        """Pack the response with its global result and the request logs."""
        outputs["result"] = result
        outputs["log"] = ctx.logger.export()

        return self._codec.pack(outputs)
