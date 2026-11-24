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


"""Faker HTTP endpoints, for humans and test tools (development & tests only).

- ``GET <any path>/files/<md5>``: the raw stored file, so what was sent and received can be
  checked in a browser (images public urls point here);
- ``POST <any path>/commit/<type>/<id>[?action=create|update|delete]``: act like the host
  application after a change: the faker commits the object to Splash (``client.commit()``).

Every other request goes to the wrapped application.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Callable, Final
from urllib.parse import parse_qs, unquote

from splashpy.dictionary import SplOperations
from splashpy.faker.objects.files import FILES_ROUTE
from splashpy.faker.store import FakerStore

if TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse, WSGIEnvironment

    from splashpy.client import SplashClient

    WsgiApp = Callable[[WSGIEnvironment, StartResponse], Iterable[bytes]]

FILES: Final = re.compile(rf"{re.escape(FILES_ROUTE)}([a-f0-9]{{32}})$")
"""Files route, at the end of the request path."""

COMMIT: Final = re.compile(r"/commit/([^/]+)/([^/]+)$")
"""Commit route, at the end of the request path."""

ACTIONS: Final = (SplOperations.CREATE, SplOperations.UPDATE, SplOperations.DELETE)
"""Commit actions accepted by the commit route."""

FAKER_USER: Final = "Splash Faker"
"""User name given with faker commits."""


class FakerHttpApp:
    """WSGI middleware serving faker files and commits."""

    def __init__(self, app: WsgiApp, store: FakerStore, client: SplashClient | None = None) -> None:
        """Wrap an application; serve the files of a faker store, and commits of a client."""
        self._app = app
        self._store = store
        self._client = client

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
        """Serve a stored file or a commit, or forward the request."""
        path = environ.get("SCRIPT_NAME", "") + environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD", "GET")
        files = FILES.search(path)
        if files is not None and method == "GET":
            return self._file(start_response, files.group(1))
        commit = COMMIT.search(path)
        if commit is not None and method == "POST" and self._client is not None:
            action = parse_qs(environ.get("QUERY_STRING", "")).get("action", [SplOperations.UPDATE])[0]
            return self._commit(start_response, unquote(commit.group(1)), unquote(commit.group(2)), action)
        return self._app(environ, start_response)

    def _file(self, start_response: StartResponse, md5: str) -> list[bytes]:
        """Send a stored file."""
        stored = self._store.load_file(md5)
        if stored is None:
            return _reply(start_response, "404 Not Found", b"Not Found", "text/plain")
        start_response(
            "200 OK",
            [
                ("Content-Type", stored.mime),
                ("Content-Length", str(stored.size)),
                ("Content-Disposition", f'inline; filename="{stored.md5}"'),
            ],
        )
        return [stored.raw]

    def _commit(self, start_response: StartResponse, object_type: str, object_id: str, action: str) -> list[bytes]:
        """Commit an object to Splash, as the host application would after a change."""
        if self._client is None or action not in ACTIONS:
            return _reply(start_response, "400 Bad Request", b"Unknown commit action", "text/plain")
        if object_type not in self._client.object_types():
            return _reply(start_response, "404 Not Found", b"Unknown object type", "text/plain")
        result = self._client.commit(object_type, object_id, action, user=FAKER_USER, comment="Faker commit")
        event = self._client.commits[-1]
        body = {"type": object_type, "id": object_id, "action": action, "result": result, "sent": event.sent}
        return _reply(start_response, "200 OK", json.dumps(body).encode(), "application/json")


def _reply(start_response: StartResponse, status: str, body: bytes, content_type: str) -> list[bytes]:
    """Send a small response."""
    start_response(status, [("Content-Type", content_type), ("Content-Length", str(len(body)))])
    return [body]
