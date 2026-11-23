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

# splashpy demo server (faker), for development & E2E tests only.

ARG PYTHON=3.12
FROM python:${PYTHON}-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir --root-user-action=ignore .

EXPOSE 8000
HEALTHCHECK --interval=2s --timeout=2s --retries=20 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/splash')"

CMD ["splashpy", "serve", "--faker", "--host", "0.0.0.0", "--port", "8000", "--path", "/splash"]
