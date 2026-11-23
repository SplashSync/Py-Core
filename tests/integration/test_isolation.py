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

"""No global state: several clients, several threads, no leak."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from splashpy import ClientInfo, SplashClient, SplashConfig
from splashpy.protocol import MessageCodec, soap


def ask_infos(client: SplashClient, codec: MessageCodec, marker: str) -> tuple[str, str, Any]:
    """Ask a client for its information, with a marker in the request."""
    payload = {"verbose": 1, "tasks": {"array-1": {"id": 1, "name": "infos", "desc": marker}}}
    body = soap.build_request("Admin", (client.config.ws_id, codec.pack(payload)), "urn:test")
    data = codec.unpack(soap.parse_response(client.handle(body)) or "")
    return marker, data["tasks"]["array-1"]["data"]["company"], data["log"]


def test_clients_and_threads_do_not_leak() -> None:
    """Each response only carries its own client data and its own request logs."""
    clients = []
    for name in ("alpha", "beta"):
        config = SplashConfig(ws_id=f"id-{name}", ws_key=f"key-{name}")
        clients.append(
            (name, SplashClient(config, info=ClientInfo(company=name)), MessageCodec(config.ws_key, config.ws_id))
        )

    jobs = [(name, client, codec, f"{name}-{i}") for i in range(40) for name, client, codec in clients]
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda job: (job[0], *ask_infos(job[1], job[2], job[3])), jobs))

    for name, marker, company, log in results:
        assert company == name
        markers = set(re.findall(r"\((\w+-\d+)\)", " ".join(log["deb"].values())))
        assert markers == {marker}
