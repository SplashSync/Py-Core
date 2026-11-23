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

"""Resolution of the fields groups order of an object.

Order: topological sort on ``after`` / ``before``, then ``priority``, then ``code``.
Every inconsistency is an error raised when the client is built, never at sync time.
"""

from __future__ import annotations

import heapq
from collections.abc import Sequence

from splashpy.objects.group import FieldsGroup, Phase


class PipelineError(ValueError):
    """Raised when fields groups cannot be ordered or own the same fields."""


def resolve(object_type: str, groups: Sequence[FieldsGroup]) -> list[FieldsGroup]:
    """Order the fields groups of an object.

    :raises PipelineError: duplicate code, unknown dependency, invalid phase or dependency cycle.
    """
    by_code: dict[str, FieldsGroup] = {}
    for group in groups:
        code = group.group_code()
        if code in by_code:
            raise PipelineError(f"{object_type}: fields group '{code}' is declared twice.")
        invalid = set(group.phases) - set(Phase.ALL)
        if invalid or not group.phases:
            raise PipelineError(f"{object_type}: fields group '{code}' has invalid phases {sorted(invalid)}.")
        by_code[code] = group
    # ====================================================================#
    # Build the dependency graph: edge "first -> then"
    successors: dict[str, set[str]] = {code: set() for code in by_code}
    for code, group in by_code.items():
        for dependency in group.after:
            _check_known(object_type, code, dependency, by_code)
            successors[dependency].add(code)
        for dependent in group.before:
            _check_known(object_type, code, dependent, by_code)
            successors[code].add(dependent)
    incoming = dict.fromkeys(by_code, 0)
    for targets in successors.values():
        for target in targets:
            incoming[target] += 1
    # ====================================================================#
    # Kahn's algorithm, ready groups taken by (priority, code)
    ready = [(by_code[code].priority, code) for code, count in incoming.items() if count == 0]
    heapq.heapify(ready)
    ordered: list[FieldsGroup] = []
    while ready:
        _, code = heapq.heappop(ready)
        ordered.append(by_code[code])
        for target in successors[code]:
            incoming[target] -= 1
            if incoming[target] == 0:
                heapq.heappush(ready, (by_code[target].priority, target))
    if len(ordered) != len(by_code):
        cycle = sorted(code for code, count in incoming.items() if count > 0)
        raise PipelineError(f"{object_type}: fields groups dependency cycle between {', '.join(cycle)}.")
    return ordered


def _check_known(object_type: str, code: str, reference: str, by_code: dict[str, FieldsGroup]) -> None:
    """Check a dependency reference exists."""
    if reference not in by_code:
        raise PipelineError(f"{object_type}: fields group '{code}' depends on unknown group '{reference}'.")
