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

from splashpy import const


class Config:

    # ====================================================================#
    # Define Module Core Configuration
    # ====================================================================#
    wsIdentifier = None
    wsIdentifier = None
    wsEncryptionKey = None
    wsTimeout = const.__TIMEOUT__
    wsCrypt = const.__CRYPT_METHOD__
    wsEncode = const.__ENCODE__
    wsHost = const.__HOST__

    # ====================================================================#
    # Various User Configurations
    # ====================================================================#
    lang = const.__LANG__
    smartNotify = const.__SMART_NOTIFY__
