# splashpy — Splash Sync Python Core

Build [Splash Sync](https://www.splashsync.com) connectors for **any Python application**.

> Branch `3.0` is a full rewrite (work in progress). splashpy 0.4.x lives on branch `1.0`.

- Wire compatible with Php-Core 3.0 (byte identical, checked by golden tests).
- No global state: one `SplashClient` per database / tenant, thread safe.
- Transport neutral: plug `client.handle_request()` in any HTTP framework; WSGI gateway included.
- Python 3.9 → 3.14, typed, one dependency (`cryptography`).

## Quick start

```python
from splashpy import SplashClient, SplashConfig, ClientInfo

client = SplashClient(
    SplashConfig(ws_id="YourWsId", ws_key="YourEncryptionKey"),
    info=ClientInfo(company="My Company", servertype="My Application"),
)

# In your HTTP endpoint (Odoo controller, Django view...)
response = client.handle_request(request_body, server_host="https://my.host", server_path="/splash")
# return response.body with response.status and response.content_type

# Notify Splash of a local change
client.commit("ThirdParty", [12], "update", user="admin", comment="Updated")
```

Any WSGI server can serve a client directly:

```python
from splashpy.adapters import make_app

application = make_app(client, path="/splash")
```

## Development

```bash
make install        # virtual environment (Python 3.9, dev tools)
make quality        # lint + style + stan + pytest
make matrix         # tests on Python 3.9 -> 3.14 (uv)
make golden         # regenerate golden fixtures with the real Php-Core (Docker)
make up             # start Splash Toolkit 3.0 + the faker on every Python version (Docker)
make test           # run the Toolkit 3.0 suites against the fakers
make stop           # stop the stack
make prune          # remove containers, volumes & built images
```

`splashpy serve --faker` runs a demo node. The faker is for development and tests only and is
never enabled implicitly.

## Documentation

- [Wire protocol](docs/protocol.md)
- [Architecture](docs/architecture.md)
- [splashpy 1.0 inventory](docs/v1-inventory.md)
- [Architecture decision records](docs/adr/)

## License

MIT — see [LICENSE](LICENSE).
