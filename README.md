# splashpy — Splash Sync Python Core

splashpy is the Python core of [Splash Sync](https://www.splashsync.com) connectors: it lets
**any Python application** expose its data to Splash, and notify Splash of its changes.

> Branch `3.0` is a full rewrite, published as pre-releases (`pip install --pre splashpy`, or
> `splashpy>=3.0.0b1`). splashpy 0.4.x lives on branch `1.0`.

## Key principles

- **Wire compatible**: output is byte identical to Php-Core 3.0, checked by golden tests.
- **No global state**: one `SplashClient` per database / tenant; each request has its own context.
- **Transport neutral**: plug the client in any HTTP framework; a WSGI gateway is provided.
- **Explicit**: no method discovery by name, no implicit extension activation.
- **Python 3.9 → 3.14**, typed, one runtime dependency (`cryptography`).

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

`splashpy serve --faker` runs a demo node. The faker is for development and tests only and is
never enabled implicitly.

## Documentation

| Page                                             | Content                                                     |
|--------------------------------------------------|-------------------------------------------------------------|
| [Getting started](docs/getting-started.md)       | Install, build a client, serve Splash requests, call Splash |
| [Configuration](docs/configuration.md)           | Settings and configuration providers                        |
| [Objects & fields groups](docs/objects.md)       | Objects, ordered fields groups, phases, values, commits     |
| [Extensions & widgets](docs/extensions.md)       | Extensions registry, hooks, widgets, faker                  |
| [Contracts](docs/contracts.md)                   | Field templates, scopes, embedded catalog and updates       |
| [Testing a connector](docs/testing.md)           | Conformance suite for connectors, commits checks            |
| [Project structure](docs/project-structure.md)   | Repository layout, package layers, request flow             |
| [Development](docs/development.md)               | Quality tools, tests, golden fixtures, Docker E2E stack, CI |

Coding agents: start with [`llms.txt`](llms.txt). The same pages ship inside the package:
`splashpy docs` prints the index, `splashpy docs <page>` one page of the installed version.

## Development

```bash
make install        # virtual environment (Python 3.9, dev tools)
make quality        # lint + style + stan + pytest
make matrix         # tests on Python 3.9 -> 3.14 (uv)
make golden         # regenerate golden fixtures with the real Php-Core (Docker)
make up             # start Splash Toolkit 3.0 + the faker on every Python version (Docker)
make test           # run the Toolkit 3.0 suites against the fakers
make manifest       # generate splash.yml, splash.json & swagger.json with the Toolkit
make stop           # stop the stack
make prune          # remove containers, volumes & built images
```

See [Development](docs/development.md) for details.

## License

MIT — see [LICENSE](LICENSE).
