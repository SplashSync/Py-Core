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

from typing import Any

import pytest

from splashpy.protocol import LegacyCipher, MessageCodec, SoapFault, XmlCodec, soap
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
