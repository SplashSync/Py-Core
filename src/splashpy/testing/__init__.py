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


"""Conformance testing of Splash clients (connectors).

- ``splashpy.testing.checks``: checks usable from any test runner (lists of problems);
- ``splashpy.testing.suite``: the pytest suite to subclass (``pip install splashpy[testing]``);
- ``splashpy.testing.values``: values generator and comparators.
"""

from __future__ import annotations

from splashpy.testing.checks import (
    NotApplicableError,
    check_description,
    check_field,
    check_fields,
    check_list,
    check_pipeline,
    expect_commit,
    roundtrip,
)
from splashpy.testing.values import ValuesGenerator, same_value, wire

__all__ = [
    "NotApplicableError",
    "ValuesGenerator",
    "check_description",
    "check_field",
    "check_fields",
    "check_list",
    "check_pipeline",
    "expect_commit",
    "roundtrip",
    "same_value",
    "wire",
]
