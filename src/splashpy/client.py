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
from splashpy.dictionary import SplFilesMethods, SplObjectMethods, SplServices
from splashpy.extensions import Extension
from splashpy.extensions.registry import ExtensionsRegistry
from splashpy.objects.base import BaseObject
from splashpy.objects.commits import CommitsManager
from splashpy.objects.events import CommitEvent
from splashpy.objects.handler import ObjectHandler
from splashpy.objects.locks import Locks
from splashpy.objects.pipeline import PipelineError
from splashpy.protocol import MessageCodec, ProtocolError, soap
from splashpy.server import ServiceHandler, TaskRunner
from splashpy.server.routers import AdminRouter
from splashpy.server.routers.files import FilesRouter
from splashpy.server.routers.objects import ObjectsRouter
from splashpy.server.routers.widgets import WidgetsRouter
from splashpy.transport import Transport, TransportError, UrllibTransport
from splashpy.widgets.base import BaseWidget

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
        objects: Iterable[BaseObject | type[BaseObject]] = (),
        widgets: Iterable[BaseWidget | type[BaseWidget]] = (),
        extensions: Iterable[Extension] = (),
        transport: Transport | None = None,
    ) -> None:
        """Build a client.

        :param config: configuration, or a provider able to build it.
        :param info: client information shown in Splash.
        :param objects: objects exposed by the host application (classes or instances).
        :param widgets: widgets exposed by the host application (classes or instances).
        :param extensions: explicitly enabled extensions (installed ones are enabled by ``config.extensions``).
        :param transport: HTTP transport for outgoing calls (``urllib`` by default).
        :raises ConfigError: when the configuration or an enabled extension is invalid.
        :raises PipelineError: when objects fields groups are inconsistent.
        """
        self.config = resolve(config)
        self.extensions = ExtensionsRegistry(extensions, self.config.extensions).all()
        self.locks = Locks()
        self._info = info or ClientInfo()
        self._transport = transport or UrllibTransport(self.config.http_user, self.config.http_password)
        self._codec = MessageCodec(self.config.ws_key, self.config.ws_id)
        self._objects = self._build_objects(objects)
        self._widgets = self._build_widgets(widgets)
        self._commits = CommitsManager(lambda: self._objects, self.extensions)
        self._handler = ServiceHandler(
            self._codec,
            TaskRunner(
                {
                    SplServices.ADMIN: AdminRouter(self),
                    SplServices.OBJECTS: ObjectsRouter(self),
                    SplServices.WIDGETS: WidgetsRouter(self),
                    SplServices.FILES: FilesRouter(self),
                }
            ),
        )

    # ====================================================================#
    # Client Description
    # ====================================================================#

    def object_types(self) -> list[str]:
        """Get available (enabled) object types, by priority then type."""
        handlers = sorted(self._objects.values(), key=lambda handler: (handler.object.priority, handler.type))
        return [handler.type for handler in handlers if not handler.object.disabled]

    def object_handler(self, object_type: str) -> ObjectHandler | None:
        """Get the handler of an available object type."""
        handler = self._objects.get(object_type)
        return handler if handler is not None and not handler.object.disabled else None

    def widget_types(self) -> list[str]:
        """Get available (enabled) widget types."""
        return [widget_type for widget_type, widget in self._widgets.items() if not widget.disabled]

    def widget(self, widget_type: str) -> BaseWidget | None:
        """Get an available widget."""
        widget = self._widgets.get(widget_type)
        return widget if widget is not None and not widget.disabled else None

    def read_file(self, ctx: RequestContext, path: str, md5: str) -> dict[str, Any] | None:
        """Read a file published by one of the objects."""
        for handler in self._objects.values():
            try:
                found = handler.object.read_file(ctx, path, md5)
            except Exception as error:
                ctx.logger.exception(error)
                continue
            if found:
                return found
        ctx.logger.error(f"File not found: {path}")
        return None

    @property
    def commits(self) -> list[CommitEvent]:
        """Recent commit events, sent or skipped (oldest first)."""
        return self._commits.history

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
        for handler in self._objects.values():
            order = " > ".join(f"{group.group_code()} ({group.origin})" for group in handler.pipeline)
            ctx.logger.debug(f"Object {handler.type}: {order}")

        return True

    def new_context(self, *, server_mode: bool = True, **kwargs: Any) -> RequestContext:
        """Create the context of a new request."""
        return RequestContext(config=self.config, server_mode=server_mode, file_reader=self.get_file, **kwargs)

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
    # Objects & Widgets Registration
    # ====================================================================#

    def _build_objects(self, objects: Iterable[BaseObject | type[BaseObject]]) -> dict[str, ObjectHandler]:
        """Register objects: host ones, then extensions ones (highest priority wins a type).

        :raises PipelineError: on equal priorities for one type, or inconsistent fields groups.
        """
        candidates: list[tuple[BaseObject, str]] = [(_instance(obj), "core") for obj in objects]
        for extension in self.extensions:
            origin = extension.name or type(extension).__name__
            candidates.extend((_instance(obj), origin) for obj in extension.objects())
        chosen: dict[str, tuple[BaseObject, str]] = {}
        for obj, origin in candidates:
            current = chosen.get(obj.object_type())
            if current is not None and current[0].priority == obj.priority:
                raise PipelineError(f"Object type {obj.object_type()} is provided twice with priority {obj.priority}.")
            if current is None or obj.priority > current[0].priority:
                chosen[obj.object_type()] = (obj, origin)
        handlers: dict[str, ObjectHandler] = {}
        ctx = self.new_context()
        for object_type, (obj, origin) in chosen.items():
            handler = ObjectHandler(obj, self.extensions, self.locks, origin)
            handler.validate(ctx)
            handlers[object_type] = handler
        return handlers

    def _build_widgets(self, widgets: Iterable[BaseWidget | type[BaseWidget]]) -> dict[str, BaseWidget]:
        """Register widgets: host ones, then extensions ones."""
        registered: dict[str, BaseWidget] = {}
        all_widgets = [*widgets, *(widget for extension in self.extensions for widget in extension.widgets())]
        for widget in all_widgets:
            instance = widget() if isinstance(widget, type) else widget
            registered[instance.widget_type()] = instance
        return registered

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

        The commit is skipped (and True returned) when the object type is unknown, when
        Splash itself is writing the object (locked), when an extension filters it, or in
        CI mode (``SPLASH_CI`` / ``SPLASH_TRAVIS`` environment variables).

        :return: False only when sending to Splash failed.
        """
        event = CommitEvent(object_type, CommitEvent.ids_of(object_ids), action, user, comment)
        ctx = self.new_context(server_mode=False)
        result = self._commits.commit(ctx, event, lambda sent: self._send_commit(sent, ctx))
        ctx.logger.flush(_LOGGER)

        return result

    def _send_commit(self, event: CommitEvent, ctx: RequestContext) -> bool:
        """Send a commit event; Php-Core only checks a result is present."""
        task = {
            "id": 1,
            "name": SplObjectMethods.COMMIT,
            "desc": f"Commit {event.action} on {event.type}",
            "params": event.params(),
        }
        response = self.call(SplServices.OBJECTS, {1: task}, ctx=ctx)

        return response is not None and "result" in response

    def get_file(self, path: str, md5: str, ctx: RequestContext | None = None) -> dict[str, Any] | None:
        """Download a file from Splash (mirror of Php-Core ``Splash::file()->getFile()``).

        :param path: file path, as received in the file or image field value.
        :param md5: file checksum, as received in the field value.
        :return: ``filename``, ``md5``, ``size`` and base64 ``raw`` contents, None on failure.
        """
        ctx = ctx or self.new_context(server_mode=False)
        task = {
            "id": 1,
            "name": SplFilesMethods.GET,
            "desc": f"Read remote file {path}",
            "params": {"file": path, "md5": md5},
        }
        response = self.call(SplServices.FILES, {1: task}, ctx=ctx)
        tasks = response.get("tasks") if response else None
        result = next(iter(tasks.values()), None) if isinstance(tasks, Mapping) else None
        if not isinstance(result, Mapping) or not php_truthy(result.get("result")):
            ctx.logger.error(f"Unable to read file {path} from Splash.")
            return None
        data = result.get("data")

        return dict(data) if isinstance(data, Mapping) else None

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


def _instance(obj: BaseObject | type[BaseObject]) -> BaseObject:
    """Instantiate an object class if needed."""
    return obj() if isinstance(obj, type) else obj


__all__ = ["HTTP_FAULT", "HTTP_OK", "SoapResponse", "SplashClient"]
