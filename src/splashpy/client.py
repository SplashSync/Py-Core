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

"""Splash client: the single entry point of a connector.

A client is built by the host application, once per database / tenant if needed.
It holds no request state: every call creates its own :class:`RequestContext`,
so one client can serve concurrent requests and several clients can live in the
same process without sharing anything.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from splashpy.config import ConfigProvider, SplashConfig, resolve
from splashpy.core.context import RequestContext, php_truthy
from splashpy.core.info import ClientInfo, server_info
from splashpy.dictionary import SplObjectMethods, SplServices
from splashpy.extensions import Extension
from splashpy.protocol import MessageCodec, ProtocolError, soap
from splashpy.server import ServiceHandler, TaskRunner
from splashpy.server.routers import AdminRouter
from splashpy.transport import Transport, TransportError, UrllibTransport

_LOGGER = logging.getLogger("splashpy")
"""Python logger receiving the Splash logs of each request."""

HTTP_OK = 200
"""HTTP status of a successful SOAP response."""

HTTP_FAULT = 500
"""HTTP status of a SOAP fault (SOAP 1.1)."""


@dataclass(frozen=True)
class SoapResponse:
    """A SOAP response ready to be sent by the host HTTP stack."""

    body: bytes
    """SOAP envelope."""

    status: int = HTTP_OK
    """HTTP status code."""

    content_type: str = "text/xml; charset=utf-8"
    """HTTP content type."""


class SplashClient:
    """A Splash node: serves requests from Splash and calls Splash."""

    # ====================================================================#
    # Constructor
    # ====================================================================#

    def __init__(
        self,
        config: SplashConfig | ConfigProvider,
        *,
        info: ClientInfo | None = None,
        extensions: Iterable[Extension] = (),
        transport: Transport | None = None,
    ) -> None:
        """Build a client.

        :param config: configuration, or a provider able to build it.
        :param info: client information shown in Splash.
        :param extensions: explicitly enabled extensions.
        :param transport: HTTP transport for outgoing calls (``urllib`` by default).
        :raises ConfigError: when the configuration is invalid.
        """
        self.config = resolve(config)
        self.extensions: tuple[Extension, ...] = tuple(sorted(extensions, key=lambda ext: (ext.priority, ext.name)))
        self._info = info or ClientInfo()
        self._transport = transport or UrllibTransport(self.config.http_user, self.config.http_password)
        self._codec = MessageCodec(self.config.ws_key, self.config.ws_id)
        self._handler = ServiceHandler(self._codec, TaskRunner({SplServices.ADMIN: AdminRouter(self)}))

    # ====================================================================#
    # Client Description
    # ====================================================================#

    def object_types(self) -> list[str]:
        """Get available object types (objects come in milestone 2)."""
        return []

    def widget_types(self) -> list[str]:
        """Get available widget types (widgets come in milestone 2)."""
        return []

    def informations(self, ctx: RequestContext) -> dict[str, Any]:
        """Get client information, completed by extensions."""
        info = replace(self._info, serverurl=self._info.serverurl or ctx.config.server_host or ctx.server_host)
        for extension in self.extensions:
            info = extension.client_info(info)

        return info.to_dict()

    def self_test(self, ctx: RequestContext) -> bool:
        """Run the client self test."""
        try:
            self.config.validate()
        except ValueError as error:
            return ctx.logger.error(str(error))
        for extension in self.extensions:
            ctx.logger.debug(f"Extension enabled: {extension.name}")

        return True

    def new_context(self, *, server_mode: bool = True, **kwargs: Any) -> RequestContext:
        """Create the context of a new request."""
        return RequestContext(config=self.config, server_mode=server_mode, **kwargs)

    # ====================================================================#
    # Incoming Requests (Splash -> this node)
    # ====================================================================#

    def handle(
        self,
        body: bytes,
        *,
        server_host: str | None = None,
        server_path: str | None = None,
        user_agent: str | None = None,
    ) -> bytes:
        """Serve a raw SOAP request and return the raw SOAP response."""
        return self.handle_request(body, server_host=server_host, server_path=server_path, user_agent=user_agent).body

    def handle_request(
        self,
        body: bytes,
        *,
        server_host: str | None = None,
        server_path: str | None = None,
        user_agent: str | None = None,
    ) -> SoapResponse:
        """Serve a raw SOAP request and return the response with its HTTP status."""
        ctx = self.new_context(server_host=server_host, server_path=server_path, user_agent=user_agent)
        try:
            call = soap.parse_request(body)
        except ProtocolError as error:
            return SoapResponse(soap.build_fault(soap.FAULT_CLIENT, str(error)), HTTP_FAULT)
        if call.service not in SplServices.ALL:
            return SoapResponse(soap.build_fault(soap.FAULT_CLIENT, f"Unknown service: {call.service}"), HTTP_FAULT)
        params = (*call.params, None, None)
        try:
            result = self._handler.handle(call.service, params[0], params[1], ctx)
        except Exception as error:
            ctx.logger.exception(error)
            ctx.logger.flush(_LOGGER)
            return SoapResponse(
                soap.build_fault(soap.FAULT_SERVER, "SOAP call: service died unexpectedly!!"), HTTP_FAULT
            )
        ctx.logger.flush(_LOGGER)

        return SoapResponse(soap.build_response(call.service, result, call.uri))

    # ====================================================================#
    # Outgoing Requests (this node -> Splash)
    # ====================================================================#

    def ping(self) -> bool:
        """Ping the Splash server (no encryption)."""
        response = self.call(SplServices.PING, None, secured=False)

        return response is not None and php_truthy(response.get("result"))

    def connect(self) -> bool:
        """Check the connection to the Splash server (encrypted)."""
        response = self.call(SplServices.CONNECT, {})

        return response is not None and php_truthy(response.get("result"))

    def commit(
        self,
        object_type: str,
        object_ids: str | int | Sequence[str | int],
        action: str,
        user: str = "",
        comment: str = "",
    ) -> bool:
        """Notify the Splash server of a local change.

        Locks and commit rules (server mode, objects locked by a running Set...)
        come with the objects layer in milestone 2.
        """
        ids = [str(object_ids)] if isinstance(object_ids, (str, int)) else [str(i) for i in object_ids]
        task = {
            "id": 1,
            "name": SplObjectMethods.COMMIT,
            "desc": f"Commit changes on {object_type}",
            "params": {"type": object_type, "id": ids, "action": action, "user": user, "comment": comment},
        }
        response = self.call(SplServices.OBJECTS, {1: task})

        return response is not None and php_truthy(response.get("result"))

    def call(
        self,
        service: str,
        tasks: Mapping[Any, Any] | None = None,
        *,
        secured: bool = True,
        ctx: RequestContext | None = None,
    ) -> dict[str, Any] | None:
        """Call a Splash service and return the decoded response (None on failure).

        Errors are logged in ``ctx`` (a new context when not given) and in the Python logger.
        """
        ctx = ctx or self.new_context(server_mode=False)
        outputs: dict[str, Any] = {
            "server": server_info(ctx),
            "service": service,
            "debug": int(ctx.debug),
            "verbose": int(ctx.logger.verbose),
        }
        if tasks is not None:
            outputs["tasks"] = dict(tasks)
            if tasks:
                outputs["taskscount"] = len(tasks)
        try:
            response = self._send(service, self._codec.pack(outputs, secured), ctx)
            decoded = self._codec.unpack(response or "", secured) if response else None
        except (ProtocolError, TransportError) as error:
            ctx.logger.error(f"Splash call {service} failed: {error}")
            decoded = None
        if decoded is None:
            ctx.logger.error(f"No response from Splash server for {service}.")
        else:
            ctx.logger.merge(decoded.get("log"))
        ctx.logger.flush(_LOGGER)

        return decoded

    def _send(self, service: str, data: str, ctx: RequestContext) -> str | None:
        """Send a packed message in a SOAP envelope and return the packed response."""
        url = self.config.ws_host
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        uri = self.config.server_host or self.config.ws_host
        body = soap.build_request(service, (self.config.ws_id, data), uri)
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{soap.soap_action(service, uri)}"',
        }
        ctx.logger.debug(f"[SOAP] Call Url= '{url}' Service='{service}'")
        raw = self._transport.post(url, body, headers, float(self.config.ws_timeout))

        return soap.parse_response(raw)


__all__ = ["HTTP_FAULT", "HTTP_OK", "SoapResponse", "SplashClient"]
