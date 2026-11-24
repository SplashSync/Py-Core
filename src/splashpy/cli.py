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

"""``splashpy`` command line: ``version``, ``serve`` (development server), ``describe``, ``contracts`` and ``docs``."""

from __future__ import annotations

import argparse
import importlib
import logging
import sys
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from splashpy.adapters import SplashWsgiApp
from splashpy.client import SplashClient
from splashpy.config import ConfigError, EnvConfig, JsonConfig, SplashConfig, resolve
from splashpy.contracts import ContractsError, ContractsProvider, FileCache, update
from splashpy.dictionary import SplContracts
from splashpy.documentation import DocsError, docs_source
from splashpy.extensions import Extension
from splashpy.faker import FAKER_WS_ID, FAKER_WS_KEY, FakerExtension
from splashpy.faker.http import FakerHttpApp
from splashpy.objects import PipelineError
from splashpy.version import __version__

if TYPE_CHECKING:
    from splashpy.faker.http import WsgiApp

_LOGGER = logging.getLogger("splashpy.cli")
"""Command line logger."""


class ThreadingWsgiServer(ThreadingMixIn, WSGIServer):
    """WSGI server handling each request in a thread."""

    daemon_threads = True


class QuietHandler(WSGIRequestHandler):
    """Request handler logging through the Python logger instead of stderr."""

    def log_message(self, format: str, *args: object) -> None:
        """Log one request."""
        _LOGGER.info("%s - %s", self.address_string(), format % args)


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    parser = argparse.ArgumentParser(prog="splashpy", description="Splash Sync Python Core.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("version", help="print the splashpy version")
    serve = commands.add_parser("serve", help="serve a Splash client over HTTP (development / tests)")
    serve.add_argument("--host", default="127.0.0.1", help="listen address (default: 127.0.0.1)")
    serve.add_argument("--port", type=int, default=8000, help="listen port (default: 8000)")
    serve.add_argument("--path", default=None, help="only serve this path (default: any)")
    serve.add_argument("--config", default=None, help="JSON configuration file (default: SPLASH_* variables)")
    serve.add_argument("--faker", action="store_true", help="enable the faker demo connector (NEVER in production)")
    describe = commands.add_parser("describe", help="show objects, their resolved fields groups pipeline, and widgets")
    describe.add_argument("--client", default=None, help="'module:attribute' returning a SplashClient (host apps)")
    describe.add_argument("--config", default=None, help="JSON configuration file (default: SPLASH_* variables)")
    describe.add_argument("--faker", action="store_true", help="describe the faker demo connector")
    describe.add_argument("--order", action="store_true", help="show the fields groups pipeline of each object")
    contracts = commands.add_parser("contracts", help="field templates & scopes catalog (Php-Scopes)")
    contracts.add_argument("action", choices=("show", "update"), help="show the catalog in use, or update the cache")
    contracts.add_argument("--version", default=SplContracts.VERSION, help="registry version (default: latest)")
    contracts.add_argument("--cache", default=None, help="cache directory (default: ~/.cache/splashpy/contracts)")
    docs = commands.add_parser("docs", help="print the documentation index, or one page (raw Markdown)")
    docs.add_argument("page", nargs="?", default=None, help="page name (default: the index)")

    return parser


def load_config(path: str | None, faker: bool) -> SplashConfig:
    """Load the configuration; the faker falls back on its development credentials."""
    try:
        return resolve(JsonConfig(path) if path else EnvConfig())
    except ConfigError:
        if not faker:
            raise
        _LOGGER.warning("No configuration found: using faker development credentials.")
        return SplashConfig(ws_id=FAKER_WS_ID, ws_key=FAKER_WS_KEY)


def serve(args: argparse.Namespace) -> int:
    """Run the development server."""
    config = load_config(args.config, args.faker)
    faker = FakerExtension() if args.faker else None
    if faker is not None:
        _LOGGER.warning("Faker connector ENABLED: development and tests only, never in production.")
    client = SplashClient(config, extensions=[faker] if faker else [])
    app: WsgiApp = SplashWsgiApp(client, path=args.path)
    if faker is not None:
        app = FakerHttpApp(app, faker.store, client)
    with make_server(args.host, args.port, app, ThreadingWsgiServer, QuietHandler) as server:
        _LOGGER.info("splashpy %s serving %s on http://%s:%s", __version__, config.ws_id, args.host, args.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            _LOGGER.info("Server stopped.")

    return 0


def load_client(args: argparse.Namespace) -> SplashClient:
    """Build the client to describe: a host factory, or a client from configuration."""
    if args.client:
        module_name, _, attribute = str(args.client).partition(":")
        target = getattr(importlib.import_module(module_name), attribute or "client")
        client = target() if callable(target) and not isinstance(target, SplashClient) else target
        if not isinstance(client, SplashClient):
            raise ConfigError(f"{args.client} is not a SplashClient.")
        return client
    extensions: list[Extension] = [FakerExtension()] if args.faker else []
    return SplashClient(load_config(args.config, args.faker), extensions=extensions)


def describe(args: argparse.Namespace) -> int:
    """Print objects (and their pipeline) and widgets of a client."""
    client = load_client(args)
    ctx = client.new_context()
    for object_type in client.object_types():
        handler = client.object_handler(object_type)
        if handler is None:  # pragma: no cover - listed types always have a handler
            continue
        print(f"{object_type} ({handler.origin})")
        if not args.order:
            continue
        for index, step in enumerate(handler.describe_pipeline(ctx), 1):
            rules = f"priority={step['priority']}"
            if step["after"]:
                rules += f" after={','.join(step['after'])}"
            if step["before"]:
                rules += f" before={','.join(step['before'])}"
            print(
                f"  {index}. {step['code']:<16} {rules:<36} phases={','.join(step['phases'])}"
                f"  origin={step['origin']}  fields: {', '.join(step['fields'])}"
            )
    print(f"Widgets: {', '.join(client.widget_types()) or '-'}")
    for error in ctx.logger.entries("err"):
        print(f"ERROR: {error}")
    return 0


def contracts(args: argparse.Namespace) -> int:
    """Show the contracts catalog in use, or download the latest one into the cache."""
    cache = FileCache(args.cache)
    if args.action == "update":
        try:
            result = update(cache, args.version)
        except ContractsError as error:
            _LOGGER.error("Contracts update failed, current catalog kept: %s", error)
            return 1
        state = "updated" if result.updated else "already up to date"
        print(f"Contracts catalog {state}: {result.version} ({result.commit}) in {cache.path}")
        return 0
    catalog = ContractsProvider(cache).catalog()
    print(f"Contracts catalog: {catalog.origin} {catalog.version} ({catalog.commit})")
    print(f"Templates: {len(catalog.templates)}, scopes: {len(catalog.scopes)}, cache: {cache.path}")
    return 0


def docs(args: argparse.Namespace) -> int:
    """Print the documentation index, or one page, of the installed splashpy version."""
    source = docs_source()
    try:
        print(source.read_page(args.page) if args.page else source.read_index())
    except DocsError as error:
        _LOGGER.error("%s", error)
        return 1
    if not args.page:
        print(f"Pages: {', '.join(source.names())} (splashpy docs <page>)")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Command line entry point."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = build_parser().parse_args(argv)
    if args.command == "version":
        print(__version__)
        return 0
    if args.command == "contracts":
        return contracts(args)
    if args.command == "docs":
        return docs(args)
    try:
        return describe(args) if args.command == "describe" else serve(args)
    except (ConfigError, ContractsError, PipelineError, ImportError, AttributeError) as error:
        _LOGGER.error("Invalid configuration: %s", error)
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
