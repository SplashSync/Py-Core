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

"""Commits: decide if a local change is sent to Splash (mirror of Php-Core ``CommitsManager``)."""

from __future__ import annotations

import os
import threading
from collections import deque
from collections.abc import Mapping, Sequence
from typing import Callable, Final

from splashpy.core.context import RequestContext
from splashpy.dictionary import SplOperations
from splashpy.extensions import Extension
from splashpy.objects.events import CommitEvent
from splashpy.objects.handler import ObjectHandler

HISTORY_SIZE: Final = 1000
"""Number of commit events kept in memory (1.0 kept them forever)."""

CI_VARIABLES: Final = ("SPLASH_TRAVIS", "SPLASH_CI")
"""Environment variables enabling CI mode: commits are never sent."""


class CommitsManager:
    """Filter, record and send commit events."""

    def __init__(
        self,
        handlers: Callable[[], Mapping[str, ObjectHandler]],
        extensions: Sequence[Extension],
        history_size: int = HISTORY_SIZE,
    ) -> None:
        """Use the client objects handlers and extensions."""
        self._handlers = handlers
        self._extensions = tuple(extensions)
        self._history: deque[CommitEvent] = deque(maxlen=history_size)
        self._mutex = threading.Lock()

    @property
    def history(self) -> list[CommitEvent]:
        """Recent commit events, sent or skipped (oldest first)."""
        with self._mutex:
            return list(self._history)

    def commit(self, ctx: RequestContext, event: CommitEvent, send: Callable[[CommitEvent], bool]) -> bool:
        """Send a commit event, unless it must be skipped.

        :return: True when sent successfully or skipped on purpose, False when sending failed.
        """
        handler = self._handlers().get(event.type)
        if handler is None:
            ctx.logger.warning(f"Module Commit Skipped: unknown object type {event.type}")
            return True
        reason = self._skip_reason(ctx, handler, event)
        sent = False
        result = True
        if reason:
            ctx.logger.debug(f"Module Commit Skipped ({event.type}, {event.action}, {'|'.join(event.ids)}): {reason}")
        else:
            result = sent = send(event)
        recorded = CommitEvent(event.type, event.ids, event.action, event.user, event.comment, sent=sent)
        with self._mutex:
            self._history.append(recorded)
        for extension in self._extensions:
            try:
                extension.on_commit(ctx, recorded)
            except Exception as error:
                ctx.logger.exception(error)
        return result

    def _skip_reason(self, ctx: RequestContext, handler: ObjectHandler, event: CommitEvent) -> str | None:
        """Why an event must not be sent, None when it must be sent."""
        if any(os.environ.get(variable) for variable in CI_VARIABLES):
            return "CI mode"
        for object_id in event.ids:
            if handler.locks.is_locked(event.type, object_id):
                return "object locked"
            if handler.is_filtered(ctx, object_id, None):
                return "object filtered"
        if event.action == SplOperations.CREATE and handler.locks.is_locked(event.type):
            return "creation locked"
        return None
