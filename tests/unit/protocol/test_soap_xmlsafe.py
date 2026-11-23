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

"""SOAP envelope and safe XML parsing."""

from __future__ import annotations

import pytest

from splashpy.protocol import SoapError, SoapFault, XmlError, soap, xmlsafe

BILLION_LAUGHS = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;">]>
<SPLASH>&lol2;</SPLASH>"""

EXTERNAL_ENTITY = b"""<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><SPLASH>&xxe;</SPLASH>"""


@pytest.mark.parametrize("document", [BILLION_LAUGHS, EXTERNAL_ENTITY, b"<!doctype html><html/>"])
def test_dtd_is_refused(document: bytes) -> None:
    """Any DTD is refused before parsing."""
    with pytest.raises(XmlError):
        xmlsafe.parse(document)


def test_size_limit() -> None:
    """Oversized documents are refused."""
    with pytest.raises(XmlError):
        xmlsafe.parse("<a>" + "x" * 100 + "</a>", max_size=50)


def test_malformed() -> None:
    """Malformed documents are refused."""
    with pytest.raises(XmlError):
        xmlsafe.parse("<a>")


def test_request_with_named_params_and_nil() -> None:
    """Params are read by position, whatever their names; nil values are None."""
    body = (
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body>'
        '<Admin><id>WSID</id><data xsi:nil="true"/></Admin></soap:Body></soap:Envelope>'
    )
    call = soap.parse_request(body)
    assert (call.service, call.params, call.uri) == ("Admin", ("WSID", None), soap.DEFAULT_URI)


def test_soap12_envelope_is_accepted() -> None:
    """SOAP 1.2 envelopes are understood."""
    body = (
        '<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"><e:Body>'
        '<m:Ping xmlns:m="urn:test"><a>1</a></m:Ping></e:Body></e:Envelope>'
    )
    assert soap.parse_request(body).service == "Ping"


@pytest.mark.parametrize(
    "body",
    [
        "<a/>",
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"/>',
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body/></soap:Envelope>',
        "not xml",
    ],
)
def test_invalid_requests(body: str) -> None:
    """Invalid envelopes are refused."""
    with pytest.raises(SoapError):
        soap.parse_request(body)


def test_nil_response_roundtrip() -> None:
    """A None result is a nil return value."""
    assert soap.parse_response(soap.build_response("Connect", None)) is None


def test_empty_response_is_an_error() -> None:
    """A response without content is refused."""
    with pytest.raises(SoapError):
        soap.parse_response(
            '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body/></soap:Envelope>'
        )


def test_response_without_return() -> None:
    """A response element without return value gives None."""
    body = (
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>'
        "<PingResponse/></soap:Body></soap:Envelope>"
    )
    assert soap.parse_response(body) is None


def test_escaping() -> None:
    """Values and fault messages are escaped."""
    assert soap.parse_response(soap.build_response("Ping", '<a href="x">&</a>')) == '<a href="x">&</a>'
    with pytest.raises(SoapFault) as fault:
        soap.parse_response(soap.build_fault(soap.FAULT_CLIENT, "<bad & wrong>"))
    assert (fault.value.code, fault.value.message) == ("Client", "<bad & wrong>")
