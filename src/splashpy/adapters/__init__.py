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

"""Thin HTTP gateways between host frameworks and :meth:`SplashClient.handle_request`."""

from __future__ import annotations

from splashpy.adapters.wsgi import SplashWsgiApp, make_app

__all__ = ["SplashWsgiApp", "make_app"]
