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

import logging
import hashlib
from Crypto.Cipher import AES
import base64
from splashpy.config import Config


def encrypt(data):
    # ====================================================================#
    # Safety Checks
    if Config.wsIdentifier is None or Config.wsEncryptionKey is None:
        return False;
    if not isinstance(data, str):
        return False;
    # ====================================================================#
    # Encrypt Data
    if Config.wsCrypt == "AES-256-CBC":
        cipher = AESCipher(Config.wsEncryptionKey, Config.wsIdentifier)
        return cipher.encrypt(data)

    return False;

def decrypt(data):
    # ====================================================================#
    # Safety Checks
    if Config.wsIdentifier is None or Config.wsEncryptionKey is None:
        return False;
    if not isinstance(data, str):
        return False;
    # ====================================================================#
    # Encrypt Data
    if Config.wsCrypt == "AES-256-CBC":
        cipher = AESCipher(Config.wsEncryptionKey, Config.wsIdentifier)
        return cipher.decrypt(data)

    return False;

class AESCipher:
    """OpenSsl "Like" AES 256  Cipher"""

    def __init__(self, key, iv):
        self.key = hashlib.sha256(key.encode('utf-8')).hexdigest()[:32].encode("utf-8")
        self.iv = hashlib.sha256(iv.encode('utf-8')).hexdigest()[:16].encode("utf-8")

    @staticmethod
    def __pad(s):
        return s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)

    @staticmethod
    def __unpad(s):
        return s[0:-ord(s[-1])]

   # __pad = lambda self, s: s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)
    #__unpad = lambda self, s: s[0:-ord(s[-1])]

    def encrypt(self, raw):
        raw = self.__pad(raw)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return base64.b64encode(base64.b64encode(cipher.encrypt(raw)))

    def decrypt(self, enc):
        enc = base64.b64decode(base64.b64decode(enc))
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return self.__unpad(cipher.decrypt(enc).decode("utf-8"))
