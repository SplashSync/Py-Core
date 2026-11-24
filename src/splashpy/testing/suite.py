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


"""Pytest conformance suite: subclass it in a connector to test its Splash client.

Usage (``pip install splashpy[testing]``)::

    from splashpy.testing.suite import ConformanceSuite

    class TestMyConnector(ConformanceSuite):
        @classmethod
        def build_client(cls) -> SplashClient:
            return build_my_client()

Each object type gets its own tests: description, fields definitions, pipeline determinism,
CRUD round trip with generated values, objects list and pagination. Changes made by the host
application are checked with ``expect_commit()`` in the connector own tests.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, ClassVar

import pytest

from splashpy.client import SplashClient
from splashpy.testing.checks import (
    NotApplicableError,
    check_description,
    check_fields,
    check_list,
    check_pipeline,
    roundtrip,
)

OBJECT_TYPE: str = "object_type"
"""Name of the parameter receiving each object type."""

_CLIENTS: dict[type, SplashClient] = {}
"""Clients built by the conformance suites, by suite class."""


class ConformanceSuite:
    """Splash conformance tests, run against the client returned by :meth:`build_client`."""

    object_types: ClassVar[Sequence[str] | None] = None
    """Object types to test (all the client object types when None)."""

    seed: ClassVar[int] = 0
    """Seed of generated values (reproducible runs)."""

    @classmethod
    def build_client(cls) -> SplashClient:
        """Build the client to test (to implement in the connector)."""
        raise NotImplementedError("Implement build_client() to return the client to test.")

    def pytest_generate_tests(self, metafunc: pytest.Metafunc) -> None:
        """Run object tests once per object type."""
        if OBJECT_TYPE in metafunc.fixturenames:
            types = list(self.object_types or self.build_client().object_types())
            metafunc.parametrize(OBJECT_TYPE, types, ids=types)

    @pytest.fixture
    def splash_client(self) -> SplashClient:
        """Get the client of this test class (built once per class)."""
        suite = type(self)
        if suite not in _CLIENTS:
            _CLIENTS[suite] = suite.build_client()
        return _CLIENTS[suite]

    # ====================================================================#
    # Client
    # ====================================================================#

    def test_self_test(self, splash_client: SplashClient) -> None:
        """The client self test passes, and it exposes at least one object."""
        ctx = splash_client.new_context()
        if not splash_client.self_test(ctx):
            pytest.fail("\n".join(ctx.logger.entries("err")) or "Self test failed.")
        if not splash_client.object_types():
            pytest.fail("The client exposes no objects.")

    # ====================================================================#
    # Objects
    # ====================================================================#

    def test_description(self, splash_client: SplashClient, object_type: str) -> None:
        """The object description is complete."""
        self._assert(check_description, splash_client, object_type)

    def test_fields(self, splash_client: SplashClient, object_type: str) -> None:
        """Every field definition is valid."""
        self._assert(check_fields, splash_client, object_type)

    def test_pipeline(self, splash_client: SplashClient, object_type: str) -> None:
        """The fields groups pipeline is deterministic."""
        self._assert(check_pipeline, splash_client, object_type)

    def test_crud(self, splash_client: SplashClient, object_type: str) -> None:
        """Generated values are written, read back identical, updated, then the object is deleted."""
        self._assert(roundtrip, splash_client, object_type, self.seed)

    def test_list(self, splash_client: SplashClient, object_type: str) -> None:
        """Created objects are listed, with meta and pagination."""
        self._assert(check_list, splash_client, object_type)

    # ====================================================================#
    # Private Methods
    # ====================================================================#

    @staticmethod
    def _assert(check: Any, client: SplashClient, object_type: str, *args: Any) -> None:
        """Run a check, skip when not applicable, fail with every problem found."""
        try:
            problems = check(client, client.new_context(), object_type, *args)
        except NotApplicableError as reason:
            pytest.skip(str(reason))
        if problems:
            pytest.fail("\n".join(problems))
