################################################################################
#
#  This file is part of SplashSync Project.
#
#  Copyright (C) Splash Sync  <www.splashsync.com>
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  For the full copyright and license information, please view the LICENSE
#  file that was distributed with this source code.
#
################################################################################

VENV        ?= .venv
PYTHON      ?= python3
DEV_PYTHON  ?= 3.9
BIN         := $(VENV)/bin
PY_VERSIONS ?= 3.9 3.10 3.11 3.12 3.13 3.14
TOOLKIT     ?= splashsync/toolkit:3.0
WS          ?= ThisIsSplashWsId3p14
MANIFESTS   := splash.yml splash.json swagger.json

.DEFAULT_GOAL := help
.PHONY: help install lint style stan pytest quality matrix contracts golden up test manifest stop prune build clean

help:		## Show this help
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

################################################################################
# Environment
################################################################################

install:	## Create the virtual environment with dev dependencies
	@if command -v uv >/dev/null; then uv venv -q --python $(DEV_PYTHON) $(VENV) && uv pip install -q --python $(BIN)/python -e ".[dev]"; \
	else $(PYTHON) -m venv $(VENV) && $(BIN)/pip install -q -e ".[dev]"; fi

################################################################################
# Quality (BadPixxel standard targets)
################################################################################

lint:		## Linters (ruff)
	$(BIN)/ruff check src tests tools

style:		## Code style (ruff format) & security (bandit)
	$(BIN)/ruff format --check src tests tools
	$(BIN)/bandit -q -c pyproject.toml -r src

stan:		## Static analysis (mypy strict)
	$(BIN)/mypy

pytest:		## Unit & integration tests with coverage
	$(BIN)/pytest --cov

quality: lint style stan pytest	## Run ALL checks

matrix:		## Run tests on every supported Python version (needs uv)
	@for v in $(PY_VERSIONS); do \
		echo "=== Python $$v"; \
		uv run -q --isolated --python $$v --with-editable ".[dev]" pytest -q || exit 1; \
	done

################################################################################
# Golden Fixtures & E2E (Docker)
################################################################################

contracts:	## Refresh the contracts catalog embedded in the package (Php-Scopes, latest)
	$(VENV)/bin/splashpy contracts update --cache src/splashpy/contracts/data

golden:		## Regenerate golden fixtures with the real Php-Core
	docker run --rm --user "$$(id -u):$$(id -g)" -v "$$PWD:/py" -w /app --entrypoint php \
		$(TOOLKIT) /py/tools/golden/generate.php /py/tests/fixtures/golden

up:		## Start Toolkit 3.0 and the Python fakers (Docker)
	docker network inspect splashsync >/dev/null 2>&1 || docker network create splashsync --attachable
	docker compose up -d --build --wait

test:		## Run the Toolkit 3.0 suites against the Python fakers (Docker)
	docker compose exec -T toolkit php vendor/bin/phpunit -c phpunit.xml.dist --testsuite Validator

manifest:	## Generate Splash manifests (splash.yml, splash.json, swagger.json) with the Toolkit (WS=...)
	docker compose exec -T toolkit bin/console splash:server:manifest --ws=$(WS)
	docker compose exec -T toolkit bin/console splash:server:swagger --ws=$(WS)
	@for file in $(MANIFESTS); do docker compose cp toolkit:/app/$$file ./$$file || exit 1; done

stop:		## Stop the Docker stack
	docker compose stop

prune:		## Remove the Docker stack: containers, volumes, built images & internal network
	docker compose down -v --rmi local --remove-orphans

################################################################################
# Build
################################################################################

build:		## Build wheel & sdist
	$(BIN)/python -m build

clean:		## Remove build & cache artefacts
	rm -rf build dist .cache .mypy_cache .ruff_cache .coverage htmlcov src/*.egg-info
