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


"""Faker files: download from Splash, storage by checksum, ReadFile and HTTP endpoint."""

from __future__ import annotations

import struct
import zlib
from collections.abc import Iterable
from typing import Any

from splashpy import RequestContext, SplashClient, SplashConfig
from splashpy.dictionary import SplServices
from splashpy.faker import FakerExtension
from splashpy.faker.http import FakerFilesApp
from splashpy.faker.store import FakerStore
from splashpy.fields import Files
from splashpy.objects.handler import ObjectHandler
from tests.support import FakeSplashServer


def png(width: int, height: int) -> bytes:
    """Build a minimal PNG header of the given size."""
    header = struct.pack(">II", width, height) + b"\x08\x02\x00\x00\x00"
    crc = struct.pack(">I", zlib.crc32(b"IHDR" + header))
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + header + crc


IMAGE = png(3, 2)
"""Remote image contents."""

PDF = b"%PDF-1.4 faker document"
"""Remote file contents."""

REMOTE = {"/remote/image.png": IMAGE, "/remote/doc.pdf": PDF, "/remote/bad.png": b"not the right contents"}
"""Files served by the fake Splash server, by path."""


def faker_client(config: SplashConfig, store: FakerStore | None = None) -> tuple[SplashClient, FakeSplashServer]:
    """Build a faker client talking to a fake Splash server."""
    server = FakeSplashServer(config, files=REMOTE)
    return SplashClient(config, extensions=[FakerExtension(store)], transport=server), server


def received(path: str, raw: bytes, name: str = "Picture") -> dict[str, Any]:
    """Build a file value, as received from Splash."""
    return {"name": name, "filename": path.rsplit("/", 1)[-1], "path": path, "md5": Files.md5(raw), "size": 1}


def read(handler: ObjectHandler | None, ctx: RequestContext, object_id: str, field_id: str) -> Any:
    """Read one field of a faker object."""
    assert handler is not None
    values = handler.get(ctx, object_id, [field_id])
    assert values is not None
    return values[field_id]


def file_reads(server: FakeSplashServer) -> int:
    """Count ReadFile calls received by the fake Splash server."""
    return sum(1 for request in server.requests if request["call"].service == SplServices.FILES)


def test_client_get_file(config: SplashConfig) -> None:
    """Files are read from Splash with path & md5; failures give None."""
    client, server = faker_client(config)
    data = client.get_file("/remote/image.png", Files.md5(IMAGE))
    assert data is not None
    assert Files.decode_raw(data["raw"]) == IMAGE
    task = server.requests[0]["inputs"]["tasks"]["array-1"]
    assert task["params"] == {"file": "/remote/image.png", "md5": Files.md5(IMAGE)}
    ctx = client.new_context(server_mode=False)
    assert client.get_file("/remote/missing.png", "x", ctx) is None
    assert ctx.logger.has_errors
    assert RequestContext(config).get_file("/remote/image.png", "x") is None


def test_faker_downloads_and_stores_files(config: SplashConfig) -> None:
    """Received files are downloaded once, stored by checksum and read back from the stored file."""
    store = FakerStore()
    client, server = faker_client(config, store)
    ctx = client.new_context(server_host="http://faker.test", server_path="/splash/")
    images = client.object_handler("image")
    assert images is not None
    picture = {**received("/remote/image.png", IMAGE), "width": 999, "url": "http://elsewhere"}
    object_id = images.set(ctx, "", {"name": "One", "picture": picture})
    assert object_id is not None
    md5 = Files.md5(IMAGE)
    assert read(images, ctx, object_id, "picture") == {
        "name": "Picture",
        "filename": "image.png",
        "path": f"faker/files/{md5}",
        "url": f"http://faker.test/splash/files/{md5}",
        "width": 3,
        "height": 2,
        "md5": md5,
        "size": len(IMAGE),
    }
    # Same contents, another name: no new download, one stored file
    assert images.set(ctx, object_id, {"thumbnail": received("/remote/image.png", IMAGE, "Thumb")}) == object_id
    assert read(images, ctx, object_id, "thumbnail")["name"] == "Thumb"
    assert file_reads(server) == 1
    # Stored files are served to Splash by path & checksum
    served = client.read_file(ctx, f"faker/files/{md5}", md5)
    assert served is not None
    assert Files.decode_raw(served["raw"]) == IMAGE
    assert client.read_file(ctx, "/remote/image.png", md5) is None
    # Files: no image dimensions
    files = client.object_handler("file")
    assert files is not None
    file_id = files.set(ctx, "", {"name": "Doc", "document": received("/remote/doc.pdf", PDF, "Doc")})
    assert file_id is not None
    document = read(files, ctx, file_id, "document")
    assert (document["size"], "width" in document) == (len(PDF), False)
    stored = store.load_file(Files.md5(PDF))
    assert stored is not None
    assert stored.mime == "application/pdf"


def test_faker_files_failures(config: SplashConfig) -> None:
    """Invalid values, failed downloads and wrong checksums are refused; empty values clear."""
    store = FakerStore()
    client, _ = faker_client(config, store)
    files = client.object_handler("file")
    assert files is not None
    invalid = (
        {"name": "No md5", "path": "/remote/doc.pdf"},
        received("/remote/missing.pdf", PDF),
        received("/remote/bad.png", PDF),
    )
    for value in invalid:
        ctx = client.new_context()
        object_id = files.set(ctx, "", {"name": "X", "document": value})
        assert object_id is not None
        assert ctx.logger.has_errors
        assert read(files, ctx, object_id, "document") is None
    assert not store.has_file(Files.md5(PDF))
    ctx = client.new_context()
    file_id = files.set(ctx, "", {"name": "X", "document": received("/remote/doc.pdf", PDF)})
    assert file_id is not None
    assert files.set(ctx, file_id, {"document": None}) == file_id
    assert read(files, ctx, file_id, "document") is None
    # A link to a file missing from the store reads as None
    record = store.load("file", file_id)
    assert record is not None
    record.data["document"] = {"name": "Lost", "filename": "lost.pdf", "md5": "0" * 32}
    store.save("file", record)
    assert read(files, ctx, file_id, "document") is None
    assert read(files, client.new_context(), file_id, "document") is None


def test_faker_files_http_endpoint() -> None:
    """Stored files are served over HTTP by checksum; other requests are forwarded."""
    store = FakerStore()
    stored = store.save_file(IMAGE)
    assert store.save_file(IMAGE) == stored
    forwarded: list[str] = []

    def inner(environ: dict[str, Any], start_response: Any) -> Iterable[bytes]:
        forwarded.append(environ["PATH_INFO"])
        start_response("200 OK", [])
        return [b"inner"]

    app = FakerFilesApp(inner, store)
    statuses: list[tuple[str, list[tuple[str, str]]]] = []

    def call(path: str, method: str = "GET") -> bytes:
        environ = {"PATH_INFO": path, "REQUEST_METHOD": method}
        return b"".join(app(environ, lambda status, headers: statuses.append((status, headers))))  # type: ignore[arg-type]

    assert call(f"/splash/files/{stored.md5}") == IMAGE
    assert statuses[-1][0] == "200 OK"
    assert ("Content-Type", "image/png") in statuses[-1][1]
    assert call(f"/splash/files/{'0' * 32}") == b"Not Found"
    assert statuses[-1][0] == "404 Not Found"
    assert call("/splash") == b"inner"
    assert call(f"/splash/files/{stored.md5}", "POST") == b"inner"
    assert forwarded == ["/splash", f"/splash/files/{stored.md5}"]
