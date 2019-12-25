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

import xml.dom.minidom
import base64

class XmlManager:

    def __init__(self):
        self.result = {}

    @staticmethod
    def to_object(xml_string):
        """Parse String to Xml a Extract Contents"""
        xml_data = xml.dom.minidom.parseString(xml_string).firstChild
        """Verify Splash Contents are here"""
        if xml_data.nodeName != "SPLASH":
            return False

        result = XmlManager.__to_object(xml_data)

        print result

        return result

    @staticmethod
    def __to_object(element):

        print(element)
        print(element.nodeName)
        print(element.nodeType)
        print(element.nodeValue)

        """Single Value Element"""
#        if element.nodeType is xml.dom.minidom.Node.TEXT_NODE:
#            return base64.b64decode(element.data)
        if element.nodeName == "#text":
            return base64.b64decode(element.data)

        result = {}
        for element in element.childNodes:
#            """Single Value Element"""
#            if element.childNodes.__len__() == 1:
#                return XmlManager.__to_object(element)

            """Node Element"""
           if element.nodeType is xml.dom.minidom.Node.ELEMENT_NODE:
                result[element.nodeName] = XmlManager.__to_object(element)

        return result



