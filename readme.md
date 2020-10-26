[![N|Solid](https://github.com/SplashSync/Php-Core/raw/master/img/github.jpg)](https://www.splashsync.com)

# Splashpy - Splash Core Module for Python
Splash Core Module for Python 3 Applications.
This module was coded to be used on all Python Applications Modules.
It is designed as a complete toolbox for Splash Python Clients Modules.  

## Features
- All Client operations are merged in a single static class *splashpy.Framework*
- Provide base classes for creating Objects,Widgets & More...
- Provide it's on Soap Server to reduce dependencies.
- Native responses to Werkzeug requests. 
- Automatically detect Module configuration from Werkzeug requests 

## Pip3 Installation
Open a command console, enter your project directory and execute the
following command to download the latest stable version of this bundle:

```bash
$ pip3 install splashpy
```

## Basic usage

Create a Splash Server & answer Werkzeug request
```python
from splashpy.server import SplashServer

def myController(self, **kw):
    # Create Splash Server
    splash_server = SplashServer(
        "SplashServerIdentifier",   # Server ID (provided by Splash)
        "SplashEncryptionKey",      # Encryption Key (provided by Splash)
        [Object1(), Object2()],     # List of Mapped Objects
        [Widget1(), Widget2()]      # List of Mapped Widgets
    )
    # Answer request
    return splash_server.fromWerkzeug(httprequest)
```

This module is part of [SplashSync](https://splashsync.com) project.