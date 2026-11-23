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

"""HTTP transports used for outgoing calls to the Splash server."""

from __future__ import annotations

from splashpy.transport.http import Transport, TransportError, UrllibTransport

__all__ = ["Transport", "TransportError", "UrllibTransport"]
