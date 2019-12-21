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

from __future__ import unicode_literals
from pysimplesoap.client import SoapClient
from core.splash import Framework

import logging
from core.encoder import *

logging.basicConfig()

from splashpy.core.security import decrypt
import base64


class SplashClient(Framework):
    __soap_client = None

    def Ping( self ):
        """Ping Splash Server, No Encryption, Just Say Hello!!"""

        client = self.__get_client()
        wsId, wsKey, wsHost = Splash.config().identifiers()

        try:
            response = client.ping(id=wsId, data="test")
        except:
            return False

        return unpack(response, False)

    def __get_client( self ):
        if self.__soap_client is None:
            wsId, wsKey, wsHost = self.config().identifiers()
            self.__soap_client = SoapClient(location=wsHost, ns=False, exceptions=False)
#                action=wsHost,  # SOAPAction
#                namespace=wsHost,
#                soap_ns='soap', ns=False, exceptions=True)

        return self.__soap_client


if __name__ == "__main__":
    import sys

    if '--ping' in sys.argv:
        print("Ping Test")



        Splash = SplashClient("ThisIsSplashWsId", "ThisIsYourEncryptionKeyForSplash")
        Splash.config().force_host("http://py.splashsync.local/ws/soap")
        print(Splash.Ping())




    if '--web2py' in sys.argv:
        # test local sample webservice exposed by web2py
        from client import SoapClient

        if not '--wsdl' in sys.argv:
            client = SoapClient(
                location="http://127.0.0.1:8000/webservices/sample/call/soap",
                action='http://127.0.0.1:8000/webservices/sample/call/soap',  # SOAPAction
                namespace="http://127.0.0.1:8000/webservices/sample/call/soap",
                soap_ns='soap', ns=False, exceptions=True)
        else:
            client = SoapClient(wsdl="http://127.0.0.1:8000/webservices/sample/call/soap?WSDL")
        response = client.Dummy()
        print('dummy', response)
        response = client.Echo(value='hola')
        print('echo', repr(response))
