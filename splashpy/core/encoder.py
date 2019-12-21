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

import hashlib
from Crypto.Cipher import AES
import base64
from splashpy.config import Config
from security import decrypt
import xml.dom.minidom


def unpack( soapdata, secured=True ):
    """Unpack Received Splash Data to Object"""

    rawData = soapdata.children().children().children().__unicode__()
    if secured is True:
        xmlString = decrypt(rawData)
    else:
        xmlString = base64.b64decode(rawData)

    if not isinstance(xmlString, str):
        return False;

    try:
        xmlData = xml.dom.minidom.parseString(xmlString).firstChild
    except:
        return False;


    data = {
        "test": "ddd"
    }

    print xmlData.nodeName
    print xmlData.attributes.values()

    for element in xmlData.childNodes:
        if element.nodeType is xml.dom.minidom.Node.ELEMENT_NODE:
            print element.firstChild.data

    print xmlData.firstChild.nodeType
    print (xmlData.firstChild.data)
#    print xmlData.firstChild.getElementsByTagName('result').__getitem__(0).nodeValue
#    print base64.b64decode(xmlData.firstChild.firstChild.data)

    return xmlString;
