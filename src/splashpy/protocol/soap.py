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

"""Minimal SOAP 1.1 implementation dedicated to the Splash envelope.

Splash only uses RPC/encoded calls with two string parameters (webservice id and
message) and a single string return value. Envelopes are written exactly like the
PHP ``SoapClient`` / ``SoapServer`` used by Php-Core. Incoming parameters are read
by position, whatever their names (``param0`` / ``param1`` for PHP, ``id`` / ``data``
for other clients).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from splashpy.protocol import xmlsafe
from splashpy.protocol.errors import SoapError, SoapFault, XmlError

# ====================================================================#
# Namespaces
# ====================================================================#

NS_SOAP11: Final = "http://schemas.xmlsoap.org/soap/envelope/"
"""SOAP 1.1 envelope namespace."""

NS_SOAP12: Final = "http://www.w3.org/2003/05/soap-envelope"
"""SOAP 1.2 envelope namespace (accepted on input)."""

NS_XSI: Final = "http://www.w3.org/2001/XMLSchema-instance"
"""XML schema instance namespace."""

DEFAULT_URI: Final = "urn:splash"
"""Namespace used for the method element when none is known."""

FAULT_SERVER: Final = "Server"
"""Fault code: error on the server side."""

FAULT_CLIENT: Final = "Client"
"""Fault code: invalid request."""

_ENVELOPE_OPEN: Final = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
    'xmlns:ns1="{uri}" xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
    'SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
    "<SOAP-ENV:Body>"
)
"""Opening of an RPC/encoded envelope, as written by PHP."""

_ENVELOPE_CLOSE: Final = "</SOAP-ENV:Body></SOAP-ENV:Envelope>\n"
"""Closing of an envelope, as written by PHP."""


@dataclass(frozen=True)
class SoapCall:
    """An incoming SOAP call."""

    service: str
    """Called method, i.e. the Splash service name."""

    params: tuple[str | None, ...]
    """Call parameters, in order."""

    uri: str
    """Namespace of the method element, echoed in the response."""


# ====================================================================#
# Server Side
# ====================================================================#


def parse_request(body: bytes | str) -> SoapCall:
    """Parse an incoming SOAP request.

    :raises SoapError: when the envelope is invalid.
    """
    method = _first_child(_body(body))
    if method is None:
        raise SoapError("SOAP request has no method.")
    uri, service = _split_tag(method.tag)
    params = tuple(_text(param) for param in method)

    return SoapCall(service=service, params=params, uri=uri or DEFAULT_URI)


def build_response(service: str, result: str | None, uri: str = DEFAULT_URI) -> bytes:
    """Build a SOAP response returning one string (or nil), as PHP ``SoapServer``."""
    value = '<return xsi:nil="true"/>' if result is None else f'<return xsi:type="xsd:string">{escape(result)}</return>'
    xml = (
        _ENVELOPE_OPEN.format(uri=escape(uri))
        + f"<ns1:{service}Response>{value}</ns1:{service}Response>"
        + _ENVELOPE_CLOSE
    )

    return xml.encode("utf-8")


def build_fault(code: str, message: str) -> bytes:
    """Build a SOAP fault, as PHP ``SoapServer::fault()``."""
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">'
        "<SOAP-ENV:Body><SOAP-ENV:Fault>"
        f"<faultcode>SOAP-ENV:{escape(code)}</faultcode>"
        f"<faultstring>{escape(message)}</faultstring>"
        "</SOAP-ENV:Fault>" + _ENVELOPE_CLOSE
    )

    return xml.encode("utf-8")


# ====================================================================#
# Client Side
# ====================================================================#


def build_request(service: str, params: tuple[str, ...], uri: str) -> bytes:
    """Build a SOAP request, as PHP ``SoapClient`` in non-WSDL mode."""
    args = "".join(
        f'<param{index} xsi:type="xsd:string">{escape(value)}</param{index}>' for index, value in enumerate(params)
    )
    xml = _ENVELOPE_OPEN.format(uri=escape(uri)) + f"<ns1:{service}>{args}</ns1:{service}>"

    return (xml + _ENVELOPE_CLOSE).encode("utf-8")


def soap_action(service: str, uri: str) -> str:
    """Build the ``SOAPAction`` HTTP header value, as PHP ``SoapClient``."""
    return f"{uri}#{service}"


def parse_response(body: bytes | str) -> str | None:
    """Parse a SOAP response and return its single return value.

    :raises SoapFault: when the response is a fault.
    :raises SoapError: when the envelope is invalid.
    """
    response = _first_child(_body(body))
    if response is None:
        raise SoapError("SOAP response is empty.")
    if _split_tag(response.tag)[1] == "Fault":
        code = response.findtext("faultcode") or response.findtext(f"{{{NS_SOAP12}}}Code") or ""
        message = response.findtext("faultstring") or response.findtext(f"{{{NS_SOAP12}}}Reason") or ""
        raise SoapFault(code.split(":")[-1], message)
    value = _first_child(response)

    return _text(value) if value is not None else None


# ====================================================================#
# Private Helpers
# ====================================================================#


def _body(document: bytes | str) -> xmlsafe.Element:
    """Parse an envelope and return its Body element."""
    try:
        envelope = xmlsafe.parse(document)
    except XmlError as error:
        raise SoapError(str(error)) from error
    namespace, name = _split_tag(envelope.tag)
    if name != "Envelope" or namespace not in (NS_SOAP11, NS_SOAP12):
        raise SoapError("Document is not a SOAP envelope.")
    body = envelope.find(f"{{{namespace}}}Body")
    if body is None:
        raise SoapError("SOAP envelope has no body.")

    return body


def escape(text: str) -> str:
    """Escape a text for an XML element content or a double quoted attribute."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _first_child(element: xmlsafe.Element) -> xmlsafe.Element | None:
    """Get the first child element, if any."""
    return next(iter(element), None)


def _split_tag(tag: str) -> tuple[str, str]:
    """Split a ``{namespace}name`` tag."""
    if tag.startswith("{"):
        namespace, _, name = tag[1:].partition("}")
        return namespace, name

    return "", tag


def _text(element: xmlsafe.Element) -> str | None:
    """Get the text of a value element, None when nil."""
    if element.get(f"{{{NS_XSI}}}nil") in ("true", "1"):
        return None

    return element.text or ""
