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

"""Splash objects: base object, ordered fields groups pipeline, locks and commits."""

from __future__ import annotations

from splashpy.objects.base import BaseObject
from splashpy.objects.discovery import discover_groups
from splashpy.objects.events import CommitEvent
from splashpy.objects.group import FieldsGroup, Phase, fields_group
from splashpy.objects.locks import Locks
from splashpy.objects.pipeline import PipelineError
from splashpy.objects.request import ObjectRequest

__all__ = [
    "BaseObject",
    "CommitEvent",
    "FieldsGroup",
    "Locks",
    "ObjectRequest",
    "Phase",
    "PipelineError",
    "discover_groups",
    "fields_group",
]
