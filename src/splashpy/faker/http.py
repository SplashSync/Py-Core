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


"""Faker HTTP endpoint: show stored files to humans (development & tests only).

``GET <any path>/files/<md5>`` returns the raw file, so what was sent and received
can be checked in a browser (images public urls point here). Every other request
goes to the wrapped application.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Callable, Final

from splashpy.faker.objects.files import FILES_ROUTE
from splashpy.faker.store import FakerStore

if TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse, WSGIEnvironment

    WsgiApp = Callable[[WSGIEnvironment, StartResponse], Iterable[bytes]]

ROUTE: Final = re.compile(rf"{re.escape(FILES_ROUTE)}([a-f0-9]{{32}})$")
"""Files route, at the end of the request path."""


class FakerFilesApp:
    """WSGI middleware serving faker stored files, by checksum."""

    def __init__(self, app: WsgiApp, store: FakerStore) -> None:
        """Wrap an application and serve the files of a faker store."""
        self._app = app
        self._store = store

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
        """Serve a stored file, or forward the request."""
        path = environ.get("SCRIPT_NAME", "") + environ.get("PATH_INFO", "")
        match = ROUTE.search(path)
        if match is None or environ.get("REQUEST_METHOD", "GET") != "GET":
            return self._app(environ, start_response)
        stored = self._store.load_file(match.group(1))
        if stored is None:
            start_response("404 Not Found", [("Content-Type", "text/plain"), ("Content-Length", "9")])
            return [b"Not Found"]
        start_response(
            "200 OK",
            [
                ("Content-Type", stored.mime),
                ("Content-Length", str(stored.size)),
                ("Content-Disposition", f'inline; filename="{stored.md5}"'),
            ],
        )
        return [stored.raw]
