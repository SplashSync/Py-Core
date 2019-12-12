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

import unittest
import random
import string

from splashpy.config import Config
from splashpy.core.security import encrypt, decrypt

rawIn = "ThisIsForTestingEncryption"
rawOut = "ckVrUmhwNVdsOUFvMXd2N2FJdWkvRW13ako5Zm50MDMxckE1QzRMYWZVVT0="


class EncryptTests(unittest.TestCase):

    def testEncrypt( self ):
        self.forceSecurity()
        self.assertEqual(rawOut, encrypt(rawIn))

    def testDecrypt( self ):
        self.forceSecurity()
        self.assertEqual(rawIn, decrypt(rawOut))

    def testEncryptAndDecrypt( self ):
        for x in range(6):
            data = ''.join(
                random.choice(string.ascii_letters + string.digits) for i in range(random.randrange(10, 1000)))
            self.assertEqual(data, decrypt(encrypt(data)))

    def forceSecurity( self ):
        Config.wsIdentifier = "ThisIsSplashWsId"
        Config.wsEncryptionKey = "ThisIsYourEncryptionKeyForSplash"

    def randomStringDigits( stringLength=6 ):
        """Generate a random string of letters and digits """
        lettersAndDigits = string.ascii_letters + string.digits
        return ''.join(random.choice(lettersAndDigits) for i in range(random.randrange(20, 40)))


if __name__ == '__main__':
    unittest.main()
