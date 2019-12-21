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

from setuptools import setup, find_packages

#import src.pycore

setup(
       name='SplashPy',
       version="0.1",
       packages=find_packages(),
       install_requires=["soap2py", "pycrypto", 'Crypto', 'pysimplesoap'],
       author='SplashSync',
       author_email='contact@splashsync.com',
       description="Foundation Package for Splash Py Clients",
       #long_description=open('README.md').read(),
       license="MIT",
       url='https://github.com/SplashSync/Php-Core',
       # Active la prise en compte du fichier MANIFEST.in
       #include_package_data=True,
       classifiers=[
              "Programming Language :: Python",
              "Development Status :: 1 - Planning",
              "License :: MIT License",
              "Natural Language :: French",
              "Operating System :: OS Independent",
              "Programming Language :: Python :: 2.7",
              "Topic :: Communications",
       ]
)
