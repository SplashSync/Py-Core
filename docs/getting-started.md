# Getting Started

## Install

```bash
pip install splashpy
```

Requires Python 3.9 or later. The only runtime dependency is `cryptography`.

## Build a client

A client is the single entry point of a connector. Build one per database / tenant if needed.

```python
from splashpy import ClientInfo, SplashClient, SplashConfig

client = SplashClient(
    SplashConfig(ws_id="YourWsId", ws_key="YourEncryptionKey"),
    info=ClientInfo(company="My Company", servertype="My Application"),
)
```

Credentials (`ws_id`, `ws_key`) are given by Splash when the server is declared. See
[Configuration](configuration.md) for every setting and for environment / JSON providers.

## Serve Splash requests

Splash calls your application with SOAP requests. Pass the raw request body to the client and
send back what it returns, from any HTTP framework:

```python
response = client.handle_request(
    request_body,                         # bytes
    server_host="https://my.host",        # public URL of your application
    server_path="/splash",                # path of this endpoint
)
# reply with response.body, response.status and response.content_type
```

`client.handle(request_body)` returns only the response body.

### WSGI

Any WSGI server can serve a client directly:

```python
from splashpy.adapters import make_app

application = make_app(client, path="/splash")
```

For multi-tenant applications, build the client per request:

```python
from splashpy.adapters import SplashWsgiApp

application = SplashWsgiApp(factory=lambda environ: build_client_for(environ["HTTP_HOST"]))
```

### Debug page

Open the Splash endpoint in a browser with the node id: `https://my.host/splash?node=<ws_id>`.
The page shows the server information and a summary (number of objects and widgets,
enabled and installed extensions), then runs the checks (self test, ping and connect to
Splash) and prints the log (errors, warnings and messages). Without the right node id, the
endpoint only shows its name.

Nothing security related is shown: no configuration, no credentials, no details of what is
synchronized. In your own framework, use
`splashpy.server.debug.is_debug_request()` and `render_debug_page()`.

## Expose objects & widgets

```python
client = SplashClient(config, objects=[Product, ThirdParty], widgets=[SalesWidget])
```

Objects are composed of ordered fields groups: see [Objects & fields groups](objects.md).
Widgets and extensions: see [Extensions & widgets](extensions.md).

## Call Splash

```python
client.ping()           # availability check, not encrypted
client.connect()        # credentials check
client.commit("ThirdParty", [12, 13], "update", user="admin", comment="Updated")
```

Calls return `True` on success. Failures never raise: they are logged on the `splashpy` Python logger.
Use `splashpy.dictionary.SplOperations` for commit actions.

## Development server

```bash
splashpy serve --host 0.0.0.0 --port 8000 --path /splash
```

Configuration comes from `SPLASH_*` environment variables, or from `--config file.json`.

`splashpy describe --order` prints the objects of a client with their resolved fields groups
pipeline (`--client my_app.splash:build_client` for your own client, `--faker` for the demo).

`splashpy serve --faker` runs a demo connector. The faker is for development and tests only: it is
never enabled unless explicitly requested.
