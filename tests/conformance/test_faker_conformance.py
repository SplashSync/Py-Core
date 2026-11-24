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


"""The conformance suite, run against the faker: the reference usage for connectors."""

from __future__ import annotations

from splashpy import SplashClient, SplashConfig
from splashpy.faker import FAKER_WS_ID, FAKER_WS_KEY, FakerExtension
from splashpy.testing.suite import ConformanceSuite


class TestFakerConformance(ConformanceSuite):
    """Every faker object passes the conformance suite."""

    @classmethod
    def build_client(cls) -> SplashClient:
        """Build a faker client."""
        return SplashClient(SplashConfig(ws_id=FAKER_WS_ID, ws_key=FAKER_WS_KEY), extensions=[FakerExtension()])
