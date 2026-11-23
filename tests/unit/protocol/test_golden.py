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

"""Golden tests: the wire layer must produce exactly what Php-Core produces."""

from __future__ import annotations

import re
from typing import Any

import pytest

from splashpy import SplashClient, SplashConfig
from splashpy.contracts import Catalog
from splashpy.core.context import RequestContext
from splashpy.fields import FieldsFactory
from splashpy.protocol import LegacyCipher, MessageCodec, SoapFault, XmlCodec, soap
from splashpy.widgets import BaseWidget, WidgetRender
from tests.conftest import load_golden

pytestmark = pytest.mark.golden

CODEC = load_golden("codec")["cases"]
CIPHER = load_golden("cipher")["cases"]
MESSAGES = load_golden("messages")["cases"]
SOAP = load_golden("soap")


@pytest.mark.parametrize("case", CODEC, ids=[case["name"] for case in CODEC])
def test_xml_encode_is_identical(case: dict[str, Any]) -> None:
    """Encoding a payload gives the exact XML of Php-Core."""
    assert XmlCodec().encode(case["payload"], declaration=True) == case["xml"]


@pytest.mark.parametrize("case", CODEC, ids=[case["name"] for case in CODEC])
def test_xml_decode_is_identical(case: dict[str, Any]) -> None:
    """Decoding Php-Core XML gives what Php-Core decodes."""
    assert XmlCodec().decode(case["xml"]) == case["decoded"]


@pytest.mark.parametrize("case", CIPHER, ids=[str(i) for i in range(len(CIPHER))])
def test_cipher_is_identical(case: dict[str, Any]) -> None:
    """Encryption gives the exact Php-Core output, and decrypts Php-Core output."""
    cipher = LegacyCipher(case["key"], case["id"])
    assert cipher.encrypt(case["plain"]) == case["cipher"]
    assert cipher.decrypt(case["cipher"]) == case["plain"] == case["roundtrip"]


@pytest.mark.parametrize("case", MESSAGES, ids=[case["name"] for case in MESSAGES])
def test_message_pack_is_identical(case: dict[str, Any]) -> None:
    """Packed messages (secured or not) are byte identical to Php-Core ones."""
    codec = MessageCodec(case["key"], case["id"])
    assert codec.pack(case["payload"]) == case["encrypted"]
    assert codec.pack(case["payload"], secured=False) == case["unsecured"]
    assert codec.unpack(case["encrypted"]) == codec.unpack(case["unsecured"], secured=False)


@pytest.mark.parametrize("case", SOAP["php_client"], ids=[case["service"] for case in SOAP["php_client"]])
def test_soap_request_is_identical(case: dict[str, Any]) -> None:
    """Outgoing requests are written like PHP SoapClient, and its requests are understood."""
    params = (case["params"]["id"], case["params"]["data"])
    uri = case["action"].split("#")[0]
    assert soap.build_request(case["service"], params, uri).decode() == case["request"]
    assert soap.soap_action(case["service"], uri) == case["action"]
    call = soap.parse_request(case["request"])
    assert (call.service, call.params, call.uri) == (case["service"], params, uri)


@pytest.mark.parametrize("case", SOAP["php_server"], ids=[case["service"] for case in SOAP["php_server"]])
def test_soap_response_is_identical(case: dict[str, Any]) -> None:
    """Responses are written like PHP SoapServer, and its responses are understood."""
    call = soap.parse_request(case["request"])
    result = f"RESPONSE-{call.service}-{call.params[0]}-{call.params[1]}"
    assert soap.build_response(call.service, result, call.uri).decode() == case["response"]
    assert soap.parse_response(case["response"]) == result


def test_soap_fault_is_identical() -> None:
    """Faults are written like PHP SoapServer, and its faults are raised."""
    message = "SOAP call: service died unexpectedly!!"
    assert soap.build_fault(soap.FAULT_SERVER, message).decode() == SOAP["php_server_fault"]
    with pytest.raises(SoapFault) as fault:
        soap.parse_response(SOAP["php_server_fault"])
    assert (fault.value.code, fault.value.message) == ("Server", message)


def test_php_client_decodes_python_response() -> None:
    """PHP SoapClient decoded a PHP response to the same value Python returns."""
    decoded = SOAP["php_client_decode"]
    assert soap.parse_response(decoded["response"]) == decoded["decoded"]


FIELDS = load_golden("fields")["cases"]
TEMPLATES = Catalog({}, load_golden("fields")["templates"], {}, "golden")
"""Field templates exported by Php-Core, as a catalog."""


def _snake(name: str) -> str:
    """Convert a Php-Core method name to its splashpy name."""
    return re.sub(r"(?<!^)([A-Z])", r"_\1", name).lower()


def _empty_as_list(value: Any) -> Any:
    """Normalize empty containers (PHP encodes empty arrays as lists)."""
    if isinstance(value, dict):
        return {key: _empty_as_list(item) for key, item in value.items()} if value else []
    if isinstance(value, list):
        return [_empty_as_list(item) for item in value]
    return value


@pytest.mark.parametrize("case", FIELDS, ids=[case["name"] for case in FIELDS])
def test_fields_definitions_are_identical(case: dict[str, Any]) -> None:
    """Replaying a FieldsFactory recipe publishes exactly what Php-Core publishes."""
    factory = FieldsFactory(TEMPLATES)
    for method, *args in case["recipe"]:
        getattr(factory, _snake(method))(*args)
    assert _empty_as_list(factory.publish()) == _empty_as_list(case["published"])


WIDGETS = load_golden("widgets")
DESCRIPTIONS = WIDGETS["descriptions"]
RENDERS = WIDGETS["renders"]


def _golden_widget(identity: dict[str, Any], blocks: list[list[Any]]) -> BaseWidget:
    """Build the Python twin of the Php-Core golden widget."""

    class GoldenWidget(BaseWidget):
        """Widget replaying a Php-Core recipe."""

        name = identity["name"]
        description = identity["description"]
        icon = identity["icon"]
        disabled = identity["disabled"]
        options = identity["options"]

        def build_parameters(self, factory: FieldsFactory, ctx: RequestContext) -> None:
            """Replay the parameters recipe."""
            for method, *args in identity["parameters"]:
                getattr(factory, _snake(method))(*args)

        def render(self, ctx: RequestContext, params: Any, output: WidgetRender) -> bool:
            """Replay the blocks recipe."""
            for method, *args in blocks:
                getattr(output.blocks, _snake(method))(*args)
            return True

    return GoldenWidget()


@pytest.mark.parametrize("case", DESCRIPTIONS, ids=[case["name"] for case in DESCRIPTIONS])
def test_widget_description_is_identical(case: dict[str, Any], config: SplashConfig) -> None:
    """A widget describes itself exactly like Php-Core, down to the XML."""
    description = _golden_widget(case["identity"], []).describe(SplashClient(config).new_context())
    assert _empty_as_list(description) == _empty_as_list(case["description"])
    assert XmlCodec().encode(description, declaration=True) == case["xml"]


@pytest.mark.parametrize("case", RENDERS, ids=[case["name"] for case in RENDERS])
def test_widget_render_is_identical(case: dict[str, Any], config: SplashConfig) -> None:
    """Replaying a BlocksFactory recipe renders exactly what Php-Core renders, down to the XML."""
    widget = _golden_widget(DESCRIPTIONS[0]["identity"], case["recipe"])
    render = widget.get(SplashClient(config).new_context(), {})
    assert render == case["render"]
    assert XmlCodec().encode(render or {}, declaration=True) == case["xml"]
