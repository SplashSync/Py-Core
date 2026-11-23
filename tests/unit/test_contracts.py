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


"""Contracts: catalog loading & checks, cache, provider, updater and command line."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from splashpy import cli
from splashpy.contracts import (
    Catalog,
    ContractsError,
    ContractsProvider,
    FileCache,
    catalog_url,
    default_catalog,
    embedded_catalog,
    update,
)
from splashpy.contracts.cache import default_cache_path
from splashpy.dictionary import SplContracts

TEMPLATE = "Splash.Templates.Test.Name"
"""Code of the test template."""


NEWER = "2099-01-01T00:00:00+00:00"
"""Generation date of test catalogs: newer than the embedded one."""


def catalog_files(commit: str = "c1", fmt: int = 1, generated_at: str = NEWER, **templates: Any) -> dict[str, bytes]:
    """Build consistent catalog files: one template, a feature scope with a base child."""
    header = {
        "format": fmt,
        "version": "1.0",
        "commit": commit,
        "generated_at": generated_at,
        "languages": ["en_US", "fr_FR"],
    }
    documents = {
        SplContracts.TEMPLATES: {
            **header,
            "templates": templates
            or {
                TEMPLATE: {
                    "code": TEMPLATE,
                    "config": {"type": "varchar", "itemtype": "http://schema.org/Thing", "itemprop": "name"},
                    "name": {"en_US": "Name", "fr_FR": "Nom"},
                    "desc": {"en_US": "Thing name"},
                }
            },
        },
        SplContracts.SCOPES: {
            **header,
            "scopes": {
                "Test.Feature": {"kind": "feature", "types": ["Product"], "children": ["Test.Base", "Test.Other"]},
                "Test.Base": {"kind": "base", "types": ["*"], "constraints": {"Name": {"template": TEMPLATE}}},
                "Test.Other": {"kind": "base", "types": ["Order"], "constraints": {"Other": {}}},
            },
        },
    }
    files = {name: json.dumps(document).encode() for name, document in documents.items()}
    index = {
        **header,
        "files": {name: {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} for name, raw in files.items()},
    }
    return {SplContracts.INDEX: json.dumps(index).encode(), **files}


# ====================================================================#
# Catalog
# ====================================================================#


def test_embedded_catalog_is_shipped_and_valid() -> None:
    """The package always embeds a complete, consistent catalog (release fails otherwise)."""
    catalog = embedded_catalog()
    assert catalog.origin == "embedded"
    assert catalog.version
    assert len(catalog.commit) == 40
    assert len(catalog.templates) > 100
    assert len(catalog.scopes) > 10
    assert all(code == template["code"] for code, template in catalog.templates.items())


def test_catalog_templates_and_scopes() -> None:
    """Templates give their configuration by language; scopes resolve by object type."""
    catalog = Catalog.load(catalog_files().get, "test")
    assert catalog.template_config(TEMPLATE, "fr_FR") == {
        "type": "varchar",
        "itemtype": "http://schema.org/Thing",
        "itemprop": "name",
        "name": "Nom",
        "desc": "Thing name",
    }
    assert catalog.template_config(TEMPLATE)["name"] == "Name"
    assert catalog.resolve("Test.Feature", "Product") == ["Test.Feature", "Test.Base"]
    assert catalog.resolve("Test.Feature", "Order") == []
    assert list(catalog.constraints("Test.Feature", "Product")) == ["Name"]
    with pytest.raises(ContractsError, match="Unknown field template"):
        catalog.template("Missing")
    with pytest.raises(ContractsError, match="Unknown scope"):
        catalog.scope("Missing")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda files: files.pop(SplContracts.INDEX), "index.json is missing"),
        (lambda files: files.update({SplContracts.INDEX: b"[]"}), "not a JSON object"),
        (lambda files: files.update({SplContracts.INDEX: b"{"}), "not valid JSON"),
        (lambda files: files.update({SplContracts.INDEX: b'{"format": 1}'}), "lists no files"),
        (lambda files: files.update({SplContracts.SCOPES: b"{}"}), "checksum"),
        (lambda files: files.pop(SplContracts.TEMPLATES), "templates.json is missing"),
    ],
)
def test_catalog_errors(change: Any, message: str) -> None:
    """Missing, corrupted or inconsistent files are refused."""
    files = catalog_files()
    change(files)
    with pytest.raises(ContractsError, match=message):
        Catalog.load(files.get, "test")


def test_catalog_structure_errors() -> None:
    """Unsupported formats, unlisted files and missing sections are refused."""
    with pytest.raises(ContractsError, match="unsupported format"):
        Catalog.load(catalog_files(fmt=2).get, "test")
    files = catalog_files()
    index = json.loads(files[SplContracts.INDEX])
    del index["files"][SplContracts.SCOPES]
    files[SplContracts.INDEX] = json.dumps(index).encode()
    with pytest.raises(ContractsError, match="not listed"):
        Catalog.load(files.get, "test")
    empty = {"format": 1}
    raw = json.dumps(empty).encode()
    entry = {"sha256": hashlib.sha256(raw).hexdigest()}
    files = {
        SplContracts.INDEX: json.dumps(
            {"format": 1, "files": {SplContracts.TEMPLATES: entry, SplContracts.SCOPES: entry}}
        ).encode(),
        SplContracts.TEMPLATES: raw,
        SplContracts.SCOPES: raw,
    }
    with pytest.raises(ContractsError, match="templates or scopes are missing"):
        Catalog.load(files.get, "test")


# ====================================================================#
# Cache & Provider
# ====================================================================#


def test_file_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Files are written atomically and read back; default path follows the environment."""
    cache = FileCache(tmp_path / "contracts")
    assert cache.read("index.json") is None
    cache.write("index.json", b"{}")
    assert cache.read("index.json") == b"{}"
    assert [path.name for path in cache.path.iterdir()] == ["index.json"]
    monkeypatch.setenv(SplContracts.CACHE_ENV, str(tmp_path / "custom"))
    assert default_cache_path() == tmp_path / "custom"
    monkeypatch.delenv(SplContracts.CACHE_ENV)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert FileCache().path == tmp_path / "xdg" / "splashpy" / "contracts"


def test_provider(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """A valid cache is used; an invalid one is ignored with a warning; no cache gives the embedded one."""
    assert ContractsProvider().catalog() is embedded_catalog()
    valid = FileCache(tmp_path / "valid")
    for name, raw in catalog_files().items():
        valid.write(name, raw)
    provider = ContractsProvider(valid)
    assert provider.catalog().origin == "cache"
    assert provider.catalog() is provider.catalog()
    broken = FileCache(tmp_path / "broken")
    broken.write(SplContracts.INDEX, b"{")
    assert ContractsProvider(broken).catalog() is embedded_catalog()
    assert "Cached contracts catalog ignored" in caplog.text
    assert ContractsProvider(FileCache(tmp_path / "empty")).catalog() is embedded_catalog()
    older = FileCache(tmp_path / "older")
    for name, raw in catalog_files("old", generated_at="2000-01-01T00:00:00+00:00").items():
        older.write(name, raw)
    assert ContractsProvider(older).catalog() is embedded_catalog()
    undated = FileCache(tmp_path / "undated")
    for name, raw in catalog_files("undated", generated_at="not a date").items():
        undated.write(name, raw)
    assert ContractsProvider(undated).catalog() is embedded_catalog()
    assert default_catalog().templates


# ====================================================================#
# Updater & Command Line
# ====================================================================#


class FakeRegistry:
    """Registry answering from catalog files, recording downloads."""

    def __init__(self, files: dict[str, bytes], fail: bool = False) -> None:
        """Serve these files (or fail)."""
        self.files = files
        self.fail = fail
        self.urls: list[str] = []

    def __call__(self, url: str) -> bytes:
        """Download a file."""
        self.urls.append(url)
        if self.fail:
            raise OSError("network down")
        return self.files[url.rsplit("/", 1)[-1]]


def test_update(tmp_path: Path) -> None:
    """Updates download only when the commit moved, and never write an invalid catalog."""
    cache = FileCache(tmp_path)
    registry = FakeRegistry(catalog_files("c1"))
    result = update(cache, "1.0", registry)
    assert (result.updated, result.commit) == (True, "c1")
    assert registry.urls[0] == catalog_url("index.json", "1.0")
    assert registry.urls[0].startswith(SplContracts.REGISTRY)
    assert len(registry.urls) == 3
    again = FakeRegistry(catalog_files("c1"))
    assert update(cache, "1.0", again).updated is False
    assert len(again.urls) == 1
    # Corrupted cache with the same commit: downloaded again
    cache.write(SplContracts.SCOPES, b"{}")
    assert update(cache, "1.0", FakeRegistry(catalog_files("c1"))).updated is True
    # New format: refused, cache unchanged
    with pytest.raises(ContractsError, match="unsupported format"):
        update(cache, "1.0", FakeRegistry(catalog_files("c2", fmt=2)))
    with pytest.raises(ContractsError, match="Unable to download"):
        update(cache, "1.0", FakeRegistry({}, fail=True))
    assert Catalog.load(cache.read, "cache").commit == "c1"
    cache.write(SplContracts.INDEX, b"not json")
    assert update(cache, "1.0", FakeRegistry(catalog_files("c3"))).commit == "c3"


def test_update_skips_the_embedded_catalog(tmp_path: Path) -> None:
    """A remote catalog identical to the embedded one is neither downloaded nor cached."""
    embedded = embedded_catalog()
    files = catalog_files(embedded.commit)
    registry = FakeRegistry(files)
    result = update(FileCache(tmp_path), fetch=registry)
    assert (result.updated, result.commit) == (False, embedded.commit)
    assert len(registry.urls) == 1
    assert list(tmp_path.iterdir()) == []
    broken = FakeRegistry({**files, SplContracts.INDEX: b"not json"})
    with pytest.raises(ContractsError, match="not valid JSON"):
        update(FileCache(tmp_path), fetch=broken)
    assert list(tmp_path.iterdir()) == []


def test_cli_contracts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """``splashpy contracts show|update`` print the catalog in use; failures keep it."""
    registry = FakeRegistry(catalog_files("c9"))
    monkeypatch.setattr("splashpy.contracts.updater.http_fetch", registry)
    assert cli.main(["contracts", "show", "--cache", str(tmp_path)]) == 0
    assert "embedded" in capsys.readouterr().out
    assert cli.main(["contracts", "update", "--cache", str(tmp_path)]) == 0
    assert "updated: 1.0 (c9)" in capsys.readouterr().out
    assert cli.main(["contracts", "show", "--cache", str(tmp_path)]) == 0
    assert "cache 1.0 (c9)" in capsys.readouterr().out
    registry.fail = True
    registry.files = catalog_files("c10")
    assert cli.main(["contracts", "update", "--cache", str(tmp_path)]) == 1
