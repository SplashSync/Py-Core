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


"""Debug page of a node (mirror of Php-Core ``soap.php?node=<WsIdentifier>``).

Opened with a GET on the Splash endpoint and the node id (``?node=<ws_id>``), it shows
the server, a summary (objects & widgets counts, extensions), checks it (self test,
ping and connect to Splash) and prints the log (errors, warnings and messages).

It NEVER shows anything security related: no encryption key, no HTTP credentials, no
logos raw contents. Secrets are only reported as configured or not. Report values are
escaped; log entries are HTML (like Splash logs) and shown as they are.
"""

from __future__ import annotations

import hmac
import platform
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from html import escape
from typing import TYPE_CHECKING, Any, Final

from splashpy.core.info import server_info
from splashpy.core.logger import Logger
from splashpy.dictionary import SplDefinition
from splashpy.extensions.registry import installed

if TYPE_CHECKING:
    from splashpy.client import SplashClient
    from splashpy.core.context import RequestContext

NODE_PARAM: Final = "node"
"""Query parameter holding the node id."""

LOG_KINDS: Final = (("err", "Errors"), ("war", "Warnings"), ("msg", "Messages"))
"""Log kinds, in display order (debug traces are never shown)."""


@dataclass
class DebugSection:
    """One section of the debug page: a title and rows of label / value."""

    title: str
    """Section title."""

    rows: list[tuple[str, str]] = field(default_factory=list)
    """Labels and values, as text."""

    def add(self, label: str, value: Any) -> DebugSection:
        """Add a row (values converted to text)."""
        self.rows.append((label, _text(value)))
        return self


def is_debug_request(client: SplashClient, node: str | None) -> bool:
    """Check if a request asks for the debug page of this node."""
    if not node:
        return False
    return hmac.compare_digest(node.encode(), client.config.ws_id.encode())


def debug_report(client: SplashClient, ctx: RequestContext) -> list[DebugSection]:
    """Build the debug report: server, summary, then checks (logged in ``ctx``)."""
    server = DebugSection("Server")
    server.add("Module", f"{SplDefinition.NAME} {SplDefinition.VERSION}").add("Python", platform.python_version())
    for key, value in server_info(ctx).items():
        server.add(key, value)

    summary = DebugSection("Summary")
    summary.add("Objects", len(client.object_types())).add("Widgets", len(client.widget_types()))
    summary.add("Extensions enabled", [extension.name for extension in client.extensions] or "none")
    summary.add("Extensions installed", sorted(installed()) or "none")

    checks = DebugSection("Checks")
    checks.add("Self test", _status(client.self_test(ctx)))
    checks.add("Ping Splash", _status(client.ping(ctx)))
    checks.add("Connect to Splash", _status(client.connect(ctx)))

    return [server, summary, checks]


def render_debug_page(client: SplashClient, ctx: RequestContext) -> str:
    """Render the debug page as a standalone HTML document (Bootstrap, dark theme)."""
    sections = debug_report(client, ctx)
    title = escape(f"{SplDefinition.NAME} - {client.config.ws_id}")
    server, *side = sections
    cards = (
        f"<div class='col-12 col-lg-8'>{_section(server)}</div>"
        f"<div class='col-12 col-lg-4 d-flex flex-column gap-3'>{''.join(_section(item) for item in side)}</div>"
    )
    return (
        "<!DOCTYPE html><html lang='en' data-bs-theme='dark'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{title}</title>"
        f"<link rel='stylesheet' href='{BOOTSTRAP_CSS}' integrity='{BOOTSTRAP_SRI}' crossorigin='anonymous'>"
        "</head><body>"
        "<nav class='navbar bg-body-tertiary border-bottom mb-3'><div class='container-fluid'>"
        f"<span class='navbar-brand mb-0 h1'>{escape(SplDefinition.NAME)}</span>"
        f"<span class='badge text-bg-secondary'>{escape(client.config.ws_id)}</span>"
        "</div></nav>"
        f"<main class='container-fluid'><div class='row g-3'>{cards}"
        f"<div class='col-12'>{_log(ctx.logger)}</div></div></main>"
        "</body></html>"
    )


# ====================================================================#
# Private Functions
# ====================================================================#

BOOTSTRAP_CSS: Final = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
"""Bootstrap stylesheet (the page stays readable without it)."""

BOOTSTRAP_SRI: Final = "sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"
"""Bootstrap stylesheet integrity hash."""

STATUS_BADGES: Final = {"OK": "text-bg-success", "FAILED": "text-bg-danger"}
"""Badge classes of checks results."""

LOG_STYLES: Final = {"err": "danger", "war": "warning", "msg": "success"}
"""Bootstrap contextual classes of log kinds."""


def _status(ok: bool) -> str:
    """Check result as text."""
    return "OK" if ok else "FAILED"


def _text(value: Any) -> str:
    """Convert a value to display text."""
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, Mapping):
        return ", ".join(f"{key}: {_text(item)}" for key, item in value.items()) or "-"
    if isinstance(value, Iterable) and not isinstance(value, str):
        return ", ".join(_text(item) for item in value) or "-"
    return str(value)


def _section(section: DebugSection) -> str:
    """Render a section as a card with a table (values escaped)."""
    rows = []
    for label, value in section.rows:
        badge = STATUS_BADGES.get(value)
        cell = f"<span class='badge {badge}'>{escape(value)}</span>" if badge else escape(value)
        rows.append(f"<tr><th class='text-nowrap w-25'>{escape(label)}</th><td class='text-break'>{cell}</td></tr>")
    return (
        f"<div class='card'><div class='card-header fw-semibold'>{escape(section.title)}</div>"
        f"<table class='table table-sm table-striped mb-0'><tbody>{''.join(rows)}</tbody></table></div>"
    )


def _log(logger: Logger) -> str:
    """Render the log, by kind. Entries are HTML (as Splash logs), shown as they are."""
    groups = []
    for kind, title in LOG_KINDS:
        entries = logger.entries(kind)
        if not entries:
            continue
        style = LOG_STYLES[kind]
        items = "".join(f"<li class='list-group-item list-group-item-{style} small'>{entry}</li>" for entry in entries)
        groups.append(
            f"<h6 class='mt-3'>{title} <span class='badge text-bg-{style}'>{len(entries)}</span></h6>"
            f"<ul class='list-group'>{items}</ul>"
        )
    body = "".join(groups) or "<p class='text-body-secondary mb-0'>Empty log.</p>"
    header = "<div class='card-header fw-semibold'>Log</div>"
    return f"<div class='card'>{header}<div class='card-body pt-0'>{body}</div></div>"
