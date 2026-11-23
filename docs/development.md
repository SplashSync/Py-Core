# Development

## Environment

```bash
make install        # .venv with Python 3.9 (uv when available) and dev tools
make help           # list every target
```

## Quality

| Target         | Tools                                              |
|----------------|----------------------------------------------------|
| `make lint`    | ruff check                                         |
| `make style`   | ruff format, bandit                                |
| `make stan`    | mypy strict, run on Python 3.9                     |
| `make pytest`  | unit & integration tests, coverage ≥ 90 %          |
| `make quality` | all of the above                                   |
| `make matrix`  | tests on Python 3.9, 3.10, 3.11, 3.12, 3.13, 3.14  |

Code rules enforced by ruff and mypy:

- every module starts with `from __future__ import annotations` (Python 3.9 floor);
- every module, class and function has a docstring;
- full type hints, `mypy --strict`;
- no `match` statement, no Python 3.10+ runtime features.

## Golden fixtures

`tests/fixtures/golden/` holds reference data produced by the **real Php-Core 3.0**: XML encoding,
encryption, complete messages, SOAP envelopes and fields definitions (FieldsFactory recipes
replayed by splashpy). Golden tests require splashpy output to be byte
identical.

```bash
make golden         # runs tools/golden/generate.php in the splashsync/toolkit:3.0 image
```

Regenerate them when Php-Core changes, and review the diff.

## Docker E2E stack

The Splash Toolkit 3.0 runs its complete `Validator` suites (admin, objects CRUD on every field
type, lists, primary keys, multi reads, widgets) against the splashpy faker, on every supported
Python version: about 1 300 tests and 140 000 assertions.

```bash
make up             # build & start the stack (creates the "splashsync" network if missing)
make test           # run the Toolkit suites
make manifest       # generate splash.yml, splash.json & swagger.json at the project root
make stop           # stop the containers
make prune          # remove containers, volumes, internal network & built images
```

`make manifest` asks the Toolkit for the Splash manifests of one connector (default
`WS=ThisIsSplashWsId3p14`, e.g. `make manifest WS=ThisIsSplashWsId3p9`) and copies them to the
project root.

To test one Python version only, filter on the connection name:

```bash
docker compose exec -T -e "SPLASH_SEQUENCE=[3.0] Python 3.12" toolkit \
    php vendor/bin/phpunit -c phpunit.xml.dist --testsuite Validator
```

Network `pycore` (`172.169.2.0/24`), also attached to the external `splashsync` network:

| Service       | Host name                | IP address     |
|---------------|--------------------------|----------------|
| toolkit       | `toolkit.splashpy.local` | 172.169.2.10   |
| python-3-9    | `3p9.splashpy.local`     | 172.169.2.39   |
| python-3-10   | `3p10.splashpy.local`    | 172.169.2.30   |
| python-3-11   | `3p11.splashpy.local`    | 172.169.2.31   |
| python-3-12   | `3p12.splashpy.local`    | 172.169.2.32   |
| python-3-13   | `3p13.splashpy.local`    | 172.169.2.33   |
| python-3-14   | `3p14.splashpy.local`    | 172.169.2.34   |

Fakers listen on port `8000`, path `/splash`. To add a Python version: a `docker/python-X.Y.yml`
file, a line in `docker-compose.yml` `include:`, a `depends_on` line in `docker/toolkit.yml` and a
connection in `docker/toolkit/splash.yaml`.

## Continuous integration

`.gitlab-ci.yml` declares the stages and includes one file per stage:

| Stage         | File                  | Jobs                                                                     |
|---------------|-----------------------|--------------------------------------------------------------------------|
| `Quality`     | `ci/Quality.yml`      | `quality`: `make lint style stan` on Python 3.9                          |
| `Functional`  | `ci/Functional.yml`   | `tests`: pytest with coverage on Python 3.9 → 3.14 (parallel matrix)     |
|               |                       | `e2e`: Docker stack + Toolkit suites (`Dedicated-Docker` runner)         |
| `Builds`      | `ci/Builds.yml`       | `release:test` (TestPyPI, manual), `release:tags` (PyPI, on tags)        |

## Branches

- `3.0`: splashpy 3.0 (this code).
- `1.0`: splashpy 0.4.x, frozen, critical fixes only.
