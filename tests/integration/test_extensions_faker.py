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

"""Extensions registry, faker connector and ``splashpy describe``."""

from __future__ import annotations

import sys
from dataclasses import replace
from types import ModuleType
from typing import Any

import pytest

from splashpy import ConfigError, Extension, SplashClient, SplashConfig, cli
from splashpy.contracts import embedded_catalog
from splashpy.extensions.registry import ExtensionsRegistry, installed
from splashpy.faker import FakerExtension
from splashpy.faker.objects import StoredGroup
from splashpy.faker.objects.thirdparty import SCOPE
from splashpy.faker.store import FakerStore, Record
from splashpy.objects import ObjectRequest

# ====================================================================#
# Registry
# ====================================================================#


def test_faker_is_installed_but_never_enabled_by_default(config: SplashConfig) -> None:
    """Installed extensions are listed, and only enabled when allowlisted."""
    assert "faker" in installed()
    client = SplashClient(config)
    assert client.object_types() == []
    assert client.widget_types() == []
    enabled = SplashClient(replace(config, extensions=("faker",)))
    assert enabled.object_types() == FAKER_TYPES
    assert [extension.name for extension in enabled.extensions] == ["faker"]


def test_registry_errors() -> None:
    """Unknown names, duplicate names and non extensions are refused."""
    with pytest.raises(ConfigError, match="not installed"):
        ExtensionsRegistry(enabled=["unknown"])
    with pytest.raises(ConfigError, match="used twice"):
        ExtensionsRegistry([FakerExtension(), FakerExtension()])
    registry = ExtensionsRegistry([FakerExtension()], enabled=["faker"])
    assert registry.names() == ["faker"]


def test_registry_refuses_non_extensions(monkeypatch: pytest.MonkeyPatch) -> None:
    """An entry point that does not give an extension is refused."""

    class Point:
        name = "bad"

        def load(self) -> Any:
            return object

    monkeypatch.setattr("splashpy.extensions.registry.installed", lambda: {"bad": Point()})
    with pytest.raises(ConfigError, match="not a splashpy extension"):
        ExtensionsRegistry(enabled=["bad"])


def test_extension_defaults(config: SplashConfig) -> None:
    """The base extension contributes nothing and hooks are neutral."""
    extension = Extension()
    ctx = SplashClient(config).new_context()
    assert (extension.objects(), extension.fields_groups(), extension.widgets()) == ((), {}, ())
    assert extension.is_filtered(ctx, "X", "1", None) is False
    description: dict[str, Any] = {}
    extension.configure_description(ctx, "X", description)
    extension.configure_fields(ctx, "X", {})
    extension.before_set(ObjectRequest(ctx, "X"))
    extension.after_set(ObjectRequest(ctx, "X"), None)
    assert description == {}


# ====================================================================#
# Faker
# ====================================================================#


def test_faker_store(tmp_path: Any) -> None:
    """Records are created, saved, listed and deleted; invalid ids are never found."""
    store = FakerStore(str(tmp_path / "faker.db"))
    record = store.create("T")
    record.data["name"] = "x"
    assert store.save("T", record)
    loaded = store.load("T", record.id)
    assert loaded is not None
    assert loaded.data == {"name": "x"}
    assert store.load("T", "abc") is None
    assert store.load("Other", record.id) is None
    assert [item.id for item in store.all("T")] == [record.id]
    store.delete("T", record.id)
    assert store.all("T") == []
    assert not store.save("T", Record("999"))


FAKER_TYPES = ["short", "simple", "list", "primary", "image", "file", "ThirdParty"]
"""Faker object types, in declaration order."""


def test_faker_objects(config: SplashConfig) -> None:
    """Only the primary object has a primary key; short has two fields; simple has no image nor file."""
    client = SplashClient(config, extensions=[FakerExtension()])
    ctx = client.new_context()
    assert client.object_types() == FAKER_TYPES
    fields = {object_type: client.object_handler(object_type).fields(ctx) for object_type in FAKER_TYPES}  # type: ignore[union-attr]
    primaries = {
        object_type for object_type, defs in fields.items() if any(field["primary"] for field in defs.values())
    }
    assert primaries == {"primary"}
    assert list(fields["short"]) == ["name", "active"]
    simple_types = {field["type"] for field in fields["simple"].values()}
    assert {"price", "inline", "objectid::short", "lang"} <= simple_types
    assert not simple_types & {"image", "file"}
    assert [field["type"] for field in fields["list"].values() if "@" in field["id"]] == [
        "bool@list",
        "varchar@list",
        "double@list",
        "price@list",
        "varchar@list",
        "varchar@list",
    ]
    templated = [field["options"].get("tmpl") for field in fields["simple"].values() if "tmpl" in field["options"]]
    assert "Splash.Templates.ThirdParty.Profile.CivilityType" in templated
    assert fields["list"]["type@items"]["options"]["tmpl"] == "Splash.Templates.Accounting.Items.Type"


def test_faker_roundtrip(config: SplashConfig) -> None:
    """Faker objects keep values as received, list, filter and identify."""
    client = SplashClient(config, extensions=[FakerExtension()])
    ctx = client.new_context()
    simple = client.object_handler("simple")
    assert simple is not None
    values = {"name": "One", "bool": "1", "title_fr_FR": "Un", "status": "draft", "colors": '["red"]'}
    object_id = simple.set(ctx, "", {**values, "secret": "hidden"})
    assert object_id is not None
    assert simple.get(ctx, object_id, [*values, "secret"]) == {"id": object_id, **values, "secret": None}
    assert simple.objects_list(ctx, "one", {})["meta"] == {"current": 1, "total": 1}
    assert simple.objects_list(ctx, "nothing", {})["meta"] == {"current": 0, "total": 0}
    assert simple.delete(ctx, object_id)
    primary = client.object_handler("primary")
    assert primary is not None
    code_id = primary.set(ctx, "", {"code": "C1", "name": "One"})
    assert primary.identify(ctx, {"code": "C1"}) == code_id
    assert primary.identify(ctx, {}) is None
    items = client.object_handler("list")
    assert items is not None
    lines = {"array-0": {"label": "A", "qty": "1.5", "price": {"ht": "1"}, "enabled": "1"}}
    list_id = items.set(ctx, "", {"name": "L", "items": lines})
    assert list_id is not None
    assert items.get(ctx, list_id, ["label@items", "qty@items"]) == {
        "id": list_id,
        "items": {"0": {"label": "A", "qty": "1.5"}},
    }
    widget = client.widget("FakerCharts")
    assert widget is not None
    rendered = widget.get(ctx, {})
    assert rendered is not None
    assert len(rendered["blocks"]) == 3


def test_faker_thirdparty_honours_its_scope(config: SplashConfig) -> None:
    """The ThirdParty object exposes every field of its declared scope, from templates."""
    client = SplashClient(config, extensions=[FakerExtension()])
    ctx = client.new_context()
    assert SCOPE in client.informations(ctx)["scopes"]
    handler = client.object_handler("ThirdParty")
    assert handler is not None
    fields = handler.fields(ctx)
    tags = {(field["itemtype"], field["itemprop"]) for field in fields.values()}
    assert len(tags) == len(fields)
    constraints = embedded_catalog().constraints(SCOPE, "ThirdParty")
    assert {(constraint["itemtype"], constraint["itemprop"]) for constraint in constraints.values()} <= tags
    assert fields["name"]["required"] is True
    object_id = handler.set(ctx, "", {"name": "ACME", "civility": "female", "region": "CA", "country": "US"})
    assert object_id is not None
    values = handler.get(ctx, object_id, ["civility_name", "region_name", "country_name"])
    assert values == {"id": object_id, "civility_name": "Female", "region_name": "CA", "country_name": "US"}


def test_faker_group_requires_a_record() -> None:
    """Faker groups only work on faker records."""
    with pytest.raises(TypeError):
        StoredGroup.read(ObjectRequest(None, "X", object="not a record"), "name")  # type: ignore[arg-type]


# ====================================================================#
# Describe Command
# ====================================================================#


def test_cli_describe_faker(capsys: pytest.CaptureFixture[str]) -> None:
    """``splashpy describe --faker --order`` prints objects pipelines and widgets."""
    assert cli.main(["describe", "--faker", "--order"]) == 0
    out = capsys.readouterr().out
    assert "simple (faker)" in out
    assert "after=basic" in out
    assert "Widgets: FakerInfos, FakerCharts" in out
    assert cli.main(["describe", "--faker"]) == 0
    assert "  1." not in capsys.readouterr().out


def test_cli_describe_host_client(config: SplashConfig, capsys: pytest.CaptureFixture[str]) -> None:
    """A host application client can be described; invalid targets fail cleanly."""
    module = ModuleType("host_app")
    module.factory = lambda: SplashClient(config, extensions=[FakerExtension()])  # type: ignore[attr-defined]
    module.client = SplashClient(config)  # type: ignore[attr-defined]
    module.other = "not a client"  # type: ignore[attr-defined]
    sys.modules["host_app"] = module
    try:
        assert cli.main(["describe", "--client", "host_app:factory"]) == 0
        assert "simple (faker)" in capsys.readouterr().out
        assert cli.main(["describe", "--client", "host_app"]) == 0
        assert cli.main(["describe", "--client", "host_app:other"]) == 2
        assert cli.main(["describe", "--client", "missing_module:x"]) == 2
    finally:
        del sys.modules["host_app"]


def test_discover_groups() -> None:
    """Parts are discovered: groups defining build(), base classes and sub packages ignored."""
    from splashpy.faker.objects.simple import SimpleBasic
    from splashpy.objects.discovery import discover_groups

    groups = discover_groups("splashpy.faker.objects.simple")
    assert [group.group_code() for group in groups] == ["advanced", "basic", "templates", "translations"]
    assert SimpleBasic in groups
    assert [group.__name__ for group in discover_groups("splashpy.faker.objects")] == ["CoreName"]
    with pytest.raises(ValueError, match="not a package"):
        discover_groups("splashpy.faker.objects.base")
