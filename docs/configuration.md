# Configuration

## Settings

`SplashConfig` is immutable: build a new instance to change a setting.

| Setting         | Default                              | Description                                                       |
|-----------------|--------------------------------------|-------------------------------------------------------------------|
| `ws_id`         | required                             | Webservice identifier of this node, given by Splash               |
| `ws_key`        | required                             | Shared encryption key, given by Splash (never printed)            |
| `ws_host`       | `https://www.splashsync.com/ws/soap` | Splash endpoint for outgoing calls (`https://` added if missing)  |
| `ws_timeout`    | `30`                                 | Timeout of outgoing calls, in seconds                             |
| `lang`          | `en_US`                              | Default language                                                  |
| `http_user`     | none                                 | HTTP basic auth user for outgoing calls                           |
| `http_password` | none                                 | HTTP basic auth password (never printed)                          |
| `server_host`   | detected from requests               | Public host of this connector, reported to Splash                 |
| `server_path`   | detected from requests               | Public path of this connector endpoint                            |
| `extensions`    | none                                 | Installed extensions to enable, by name (nothing enabled implicitly) |

Invalid settings raise `ConfigError` when the client is built.

## Providers

A client accepts a `SplashConfig` or any provider with a `load()` method.

### Static

```python
from splashpy import SplashClient, SplashConfig, StaticConfig

client = SplashClient(StaticConfig(SplashConfig(ws_id="...", ws_key="...")))
```

### Environment variables

`EnvConfig` reads `SPLASH_` + the upper case setting name:

```bash
export SPLASH_WS_ID=YourWsId
export SPLASH_WS_KEY=YourEncryptionKey
export SPLASH_WS_HOST=https://www.splashsync.com/ws/soap
export SPLASH_EXTENSIONS=extension-a,extension-b
```

```python
from splashpy import EnvConfig, SplashClient

client = SplashClient(EnvConfig())                  # or EnvConfig(prefix="MYAPP_SPLASH_")
```

### JSON file

```json
{
    "ws_id":        "YourWsId",
    "ws_key":       "YourEncryptionKey",
    "extensions":   ["extension-a"]
}
```

```python
from splashpy import JsonConfig, SplashClient

client = SplashClient(JsonConfig("/etc/myapp/splash.json"))
```

Unknown keys are refused.

### Custom provider

Host applications can store settings anywhere (database, system parameters...):

```python
class MyConfig:
    def load(self) -> SplashConfig:
        return SplashConfig(ws_id=read_param("splash.id"), ws_key=read_param("splash.key"))
```
