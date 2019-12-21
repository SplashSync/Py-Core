# -*- coding: utf-8 -*-
#
#  This file is part of SplashSync Project.
#
#  Copyright (C) 2015-2019 Splash Sync  <www.splashsync.com>
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  For the full copyright and license information, please view the LICENSE
#  file that was distributed with this source code.
#

from config import Config

class Framework:
    """Base Class for Splash Client & Server"""

    __config = None
    __objects = None
    __widgets = None

    def __init__(self, identifier, key, objects=None, widgets=None, config=False):
        """Init of Splash Mini Framework"""
        Config(identifier, key)
        self.__config = Config(identifier, key)
        self.__objects = objects
        self.__widgets = widgets

    def config(self):
        """Safe Access to Local Configuration"""
        return self.__config;
