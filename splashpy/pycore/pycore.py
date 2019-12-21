# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

if __name__ == "__main__":
    print("Hello World")

#import zeep

print("This line will be printed.!!")


#import SOAPpy
#import base64 
#
#server = SOAPpy.SOAPProxy('http://localhost/Dolibarr/Dol-6.0/custom/splash/vendor/splash/phpcore/soap.php')
#ping = server.Ping(id = 'f65cf71a7ebd4281')
#print ping
#
#decoded = base64.b64decode(ping)
#print decoded
##
##
###print base64.b64decode("MQ==")
##
##
##
#from lxml import etree
#from lxml import objectify
#
#main = objectify.XML(decoded)
#
#
##main = etree.XML(decoded)
##
#print main.tag
#print main.result.tag
#print main.result.text
#

#data = ["SPLASH"]
#print data
#print(etree.tostring(data, pretty_print=True))

#import hashlib
#key = hashlib.sha256(b'f65cf71a7ebd4281')
#iv = hashlib.sha256(b'NWE0ZDRkMDE1MWRkNjguMDc2NTExNzk1YTRkNGQwMTUxZjU5NS')
#
#from Crypto.Cipher import AES
### Encryption
#encryption_suite = AES.new(key.hexdigest()[0:16], AES.MODE_CBC, iv.hexdigest()[0:16])
#cipher_text = encryption_suite.encrypt("A really secret message. Not for prying eyes.")
##
### Decryption
##decryption_suite = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
##plain_text = decryption_suite.decrypt(cipher_text)
#
#
#server = SOAPpy.SOAPProxy('http://localhost/Dolibarr/Dol-6.0/custom/splash/vendor/splash/phpcore/soap.php')
#connect = server.Connect(id = 'f65cf71a7ebd4281', data= decoded)
#print connect

import unittest

class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

class TestStringMethods2(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)
            
if __name__ == '__main__':
    unittest.main()
    
#for child in main:
#    print(child.tag)
#    print(child.text)
    

#print(main['SPLASH'])

#from zeep import Client
#
#client = Client('http://localhost/Dolibarr/Dol-6.0/custom/splash/vendor/splash/phpcore/soap.php?node=f65cf71a7ebd4281')
#
#node = client.create_message(client.service, 'myOperation', user='1')
#print(node)

#result = client.service.Ping(id='f65cf71a7ebd4281')