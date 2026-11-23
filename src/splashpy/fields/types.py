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

"""Field types, properties, sync modes and constraints (mirror of Php-Core dictionaries)."""

from __future__ import annotations

from typing import Final


class FieldType:
    """Splash field types (Php-Core ``SplFields``)."""

    BOOL: Final = "bool"
    """Boolean, transmitted as ``1`` / ``0``."""

    INT: Final = "int"
    """Signed integer."""

    DOUBLE: Final = "double"
    """Float value."""

    VARCHAR: Final = "varchar"
    """Short text (below 256 characters)."""

    TEXT: Final = "text"
    """Long text."""

    EMAIL: Final = "email"
    """Email address."""

    PHONE: Final = "phone"
    """Phone number."""

    DATE: Final = "date"
    """Date, ``Y-m-d``."""

    DATETIME: Final = "datetime"
    """Date and time, ``Y-m-d H:i:s``."""

    LANG: Final = "lang"
    """ISO language code (``en_US``)."""

    COUNTRY: Final = "country"
    """ISO country code (``FR``)."""

    STATE: Final = "state"
    """ISO state code (``CA``)."""

    CURRENCY: Final = "currency"
    """ISO currency code (``EUR``)."""

    URL: Final = "url"
    """External URL."""

    FILE: Final = "file"
    """File: name, filename, path, url, md5, size."""

    IMAGE: Final = "image"
    """Image: file keys plus width & height."""

    STREAM: Final = "stream"
    """Stream: file keys plus ttl (days)."""

    MVARCHAR: Final = "mvarchar"
    """Deprecated multi-language short text."""

    MTEXT: Final = "mtext"
    """Deprecated multi-language long text."""

    PRICE: Final = "price"
    """Price: base, ht, ttc, vat, tax, code, symbol, name."""

    LIST: Final = "list"
    """List marker: types are declared ``type@list``."""

    INLINE: Final = "inline"
    """Inline list, a JSON array of strings."""

    OBJECT_ID: Final = "objectid"
    """Object identifier, declared ``objectid::Type``, shared ``id::Type``."""

    ALL: Final = (
        VARCHAR,
        TEXT,
        BOOL,
        INT,
        DOUBLE,
        EMAIL,
        PHONE,
        DATE,
        DATETIME,
        LANG,
        COUNTRY,
        STATE,
        CURRENCY,
        URL,
        FILE,
        IMAGE,
        STREAM,
        MVARCHAR,
        MTEXT,
        PRICE,
        INLINE,
        OBJECT_ID,
    )
    """Every field type (lists excluded)."""

    PRIMARY: Final = (VARCHAR, TEXT, EMAIL, PHONE, URL, COUNTRY)
    """Types allowed as primary keys."""

    MULTI_LANG: Final = (VARCHAR, TEXT, INLINE, BOOL, INT, DOUBLE, URL)
    """Types allowed as multi-language fields."""

    @staticmethod
    def object_id(object_type: str) -> str:
        """Build the type of an object identifier field, e.g. ``objectid::ThirdParty``."""
        return f"{FieldType.OBJECT_ID}::{object_type}"


class FieldProps:
    """Keys of a published field definition (Php-Core ``SplFieldProps``)."""

    TYPE: Final = "type"
    ID: Final = "id"
    NAME: Final = "name"
    DESC: Final = "desc"
    GROUP: Final = "group"
    REQUIRED: Final = "required"
    READ: Final = "read"
    WRITE: Final = "write"
    INDEX: Final = "index"
    IN_LIST: Final = "inlist"
    HIDDEN_IN_LIST: Final = "hlist"
    LOG: Final = "log"
    PRIMARY: Final = "primary"
    SYNC_MODE: Final = "syncmode"
    MICRODATA_URL: Final = "itemtype"
    MICRODATA_PROP: Final = "itemprop"
    TAG: Final = "tag"
    CHOICES: Final = "choices"
    ASSO: Final = "asso"
    OPTIONS: Final = "options"
    NO_TEST: Final = "notest"


class SyncMode:
    """Preferred synchronization direction (Php-Core ``SplSyncMode``)."""

    BOTH: Final = "both"
    READ: Final = "export"
    WRITE: Final = "import"
    NONE: Final = "none"
    ALL: Final = (BOTH, READ, WRITE, NONE)


class FieldConstraints:
    """Field option keys used as constraints (Php-Core ``SplFieldConstraints``)."""

    TEMPLATE: Final = "tmpl"
    ALT_TAGS: Final = "altTags"
    LENGTH_MIN: Final = "minLength"
    LENGTH_MAX: Final = "maxLength"
    CASE_LOWER: Final = "isLowerCase"
    CASE_UPPER: Final = "isUpperCase"
    HTML: Final = "isHtml"
    SORT_ASC: Final = "isOrdered"
    SORT_DESC: Final = "isOrderedReverse"
    LANGUAGE: Final = "language"
