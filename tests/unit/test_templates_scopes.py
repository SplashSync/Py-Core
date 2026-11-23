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


"""Contracts in use: field templates in the factory, scopes declared in client information."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from splashpy import ClientInfo, ConfigError, Extension, SplashClient, SplashConfig
from splashpy.contracts import ContractsError, embedded_catalog
from splashpy.fields import FieldsFactory, FieldType, ObjectField
from splashpy.objects import BaseObject, FieldsGroup, ObjectRequest, fields_group

CIVILITY = "Splash.Templates.ThirdParty.Profile.CivilityType"
"""A template with choices."""

SCOPE = "Splash.Scopes.ThirdParty.Provider"
"""A published scope."""


# ====================================================================#
# Field Update (Php-Core AbstractField::update)
# ====================================================================#


def test_field_update_rules() -> None:
    """Only valid values are applied; choices and associations are replaced; the tag is kept."""
    field = ObjectField(FieldType.VARCHAR, "code").set_name("Code")
    field.add_choice("old", "Old")
    field.update(
        {
            "type": "",
            "name": 12,
            "required": "1",
            "read": "0",
            "index": [True],
            "log": 1,
            "inlist": True,
            "hlist": False,
            "syncmode": "export",
            "itemtype": "http://schema.org/Thing",
            "itemprop": "name",
            "tag": "ignored",
            "options": {"maxLength": 5, "": "no key", "empty": 0, "list": [1]},
            "choices": [{"key": "a", "value": "A"}, {"key": "b"}, "c"],
            "asso": ["other", "", 3],
            "notest": True,
        }
    )
    published = field.to_dict()
    assert (published["type"], published["name"]) == ("varchar", "Code")
    assert (published["required"], published["read"], published["index"], published["log"]) == (
        True,
        False,
        False,
        True,
    )
    assert (published["inlist"], published["hlist"], published["syncmode"]) == (True, False, "export")
    assert published["tag"] != "ignored"
    assert published["options"] == {"maxLength": 5}
    assert published["choices"] == [{"key": "a", "value": "A"}]
    assert (published["asso"], published["notest"]) == (["other"], True)
    untagged = ObjectField(FieldType.VARCHAR, "free").update({"tag": "a" * 32, "choices": "not a list"})
    assert untagged.tag == "a" * 32
    assert untagged.update({"itemtype": [], "itemprop": "x"}).item_type is None
    assert ObjectField(FieldType.BOOL, "t").update({"primary": True}).errors


# ====================================================================#
# Templates in the Factory
# ====================================================================#


def test_factory_templates() -> None:
    """Templates apply the catalog definition in the factory language, and record their code."""
    factory = FieldsFactory(embedded_catalog())
    factory.create_from_template("civility", CIVILITY, "My Civility")
    factory.set_default_language("fr_FR").create(FieldType.TEXT, "other").template(CIVILITY)
    fields = factory.publish()
    assert fields["civility"]["name"] == "My Civility"
    assert fields["civility"]["options"] == {"tmpl": CIVILITY}
    assert [choice["key"] for choice in fields["civility"]["choices"]] == ["male", "female", "neutral"]
    assert (fields["other"]["type"], fields["other"]["name"]) == ("varchar", "Type Civil")
    with pytest.raises(ContractsError, match="Unknown field template"):
        FieldsFactory().create(FieldType.VARCHAR, "x").template("Splash.Templates.Missing")


def test_unknown_template_fails_when_the_client_is_built(config: SplashConfig) -> None:
    """An unknown template is an explicit startup error, never a runtime one."""

    @fields_group("core")
    class Broken(FieldsGroup):
        def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
            factory.create_from_template("name", "Splash.Templates.Missing")

        def get(self, req: ObjectRequest, field_id: str) -> Any:
            return None

    class Thing(BaseObject):
        groups = (Broken,)

    with pytest.raises(ContractsError, match=r"Splash\.Templates\.Missing"):
        SplashClient(config, objects=[Thing])


# ====================================================================#
# Scopes
# ====================================================================#


def test_declared_scopes(config: SplashConfig) -> None:
    """Declared scopes are published in client information; unknown ones are refused."""
    client = SplashClient(config, info=replace(ClientInfo(), scopes=[SCOPE]))
    assert client.informations(client.new_context())["scopes"] == [SCOPE]
    with pytest.raises(ConfigError, match=r"Splash\.Scopes\.Missing"):
        SplashClient(config, info=replace(ClientInfo(), scopes=["Splash.Scopes.Missing"]))

    class Declaring(Extension):
        name = "declaring"

        def client_info(self, info: ClientInfo) -> ClientInfo:
            return replace(info, scopes=[*info.scopes, "Splash.Scopes.Unknown"])

    with pytest.raises(ConfigError, match=r"Splash\.Scopes\.Unknown"):
        SplashClient(config, extensions=[Declaring()])
