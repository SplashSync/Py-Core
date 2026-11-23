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

"""Task routers, one per Splash service."""

from __future__ import annotations

from splashpy.server.routers.admin import AdminRouter, AdminSource
from splashpy.server.routers.base import TaskRouter, empty_response, task_params

__all__ = ["AdminRouter", "AdminSource", "TaskRouter", "empty_response", "task_params"]
