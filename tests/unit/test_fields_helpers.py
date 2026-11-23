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

"""Fields, values helpers, pipeline resolution, widgets blocks."""

from __future__ import annotations

import base64
import struct
import zlib
from datetime import date, datetime
from itertools import permutations
from typing import Any

import pytest

from splashpy.fields import (
    Dates,
    FieldsFactory,
    FieldType,
    Files,
    Images,
    Inline,
    Lists,
    ObjectField,
    ObjectIds,
    Prices,
)
from splashpy.objects import FieldsGroup, Phase, PipelineError, fields_group
from splashpy.objects.pipeline import resolve
from splashpy.widgets import BlocksFactory

# ====================================================================#
# Helpers
# ====================================================================#


def test_lists_and_object_ids() -> None:
    """List ids and object ids encode and decode."""
    assert Lists.encode("lines", "sku") == "sku@lines"
    assert Lists.encode("", "sku") is None
    assert (Lists.field_name("sku@lines"), Lists.list_name("sku@lines")) == ("sku", "lines")
    assert Lists.explode("a@b@c") is None
    assert not Lists.is_list("sku")
    assert ObjectIds.encode("ThirdParty", 12) == "12::ThirdParty"
    assert ObjectIds.encode("ThirdParty", "") is None
    assert (ObjectIds.id("12::ThirdParty"), ObjectIds.type("12::ThirdParty")) == ("12", "ThirdParty")
    assert ObjectIds.explode("12") is None
    assert FieldType.object_id("ThirdParty") == "objectid::ThirdParty"


def test_inline() -> None:
    """Inline lists are PHP compatible JSON."""
    assert Inline.from_list([]) == "[]"
    assert Inline.from_list(["a/b", "é"]) == '["a\\/b","é"]'
    assert Inline.from_list({"x": "a"}) == '["a"]'
    assert Inline.to_list('["a","b"]') == ["a", "b"]
    assert Inline.to_list('{"k":"v"}') == ["v"]
    assert Inline.to_list("not json") == []
    assert Inline.to_list('"string"') == []
    assert Inline.to_list(None) == []


def test_dates() -> None:
    """Splash dates formats."""
    assert Dates.to_date(date(2026, 1, 2)) == "2026-01-02"
    assert Dates.to_date(None) == ""
    assert Dates.to_datetime(datetime(2026, 1, 2, 3, 4, 5)) == "2026-01-02 03:04:05"
    assert Dates.to_datetime(None) == ""
    assert Dates.parse_date("2026-01-02 10:00:00") == date(2026, 1, 2)
    assert Dates.parse_date("bad") is None
    assert Dates.parse_date("") is None
    assert Dates.parse_datetime("2026-01-02") == datetime(2026, 1, 2)
    assert Dates.parse_datetime("bad") is None
    assert Dates.parse_datetime(None) is None


def test_prices() -> None:
    """Prices encode, validate and compare like Php-Core."""
    excl = Prices.encode(100.0, 20.0, code="EUR")
    assert excl == {
        "vat": 20.0,
        "code": "EUR",
        "symbol": "",
        "name": "",
        "base": 0,
        "ht": 100.0,
        "tax": 20.0,
        "ttc": 120.0,
    }
    incl = Prices.encode(None, 20.0, 120.0, "EUR")
    assert incl is not None
    assert incl["base"] == 1
    assert incl["ht"] == pytest.approx(100.0)
    for invalid in (
        Prices.encode(None, 20.0, None, "EUR"),
        Prices.encode(1.0, 20.0, 1.0, "EUR"),
        Prices.encode(1.0, -1.0, code="EUR"),
        Prices.encode(1.0, 1.0),
    ):
        assert invalid is None
    decoded = {key: str(value) for key, value in excl.items()}
    assert Prices.is_valid(decoded)
    assert Prices.compare(excl, decoded)
    assert not Prices.compare(excl, incl)
    assert not Prices.compare(excl, {**decoded, "ht": "101"})
    assert not Prices.compare(excl, {**decoded, "code": "USD"})
    assert Prices.compare(excl, {**decoded, "code": ""})
    assert not Prices.is_valid({**decoded, "ht": "abc"})
    assert not Prices.is_valid({"ht": "1"})
    assert not Prices.is_valid("price")
    assert Prices.extract(decoded, "ttc") == 120.0
    assert Prices.extract(decoded, "missing") is None
    assert Prices.extract("x") is None


def _png(width: int, height: int) -> bytes:
    """Build a minimal PNG."""
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    chunk = b"IHDR" + header
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", len(header)) + chunk + struct.pack(">I", zlib.crc32(chunk))


IMAGES: dict[str, tuple[bytes, tuple[int, int]]] = {
    "png": (_png(3, 2), (3, 2)),
    "gif": (b"GIF89a" + struct.pack("<HH", 5, 4) + b"\x00" * 10, (5, 4)),
    "bmp": (b"BM" + b"\x00" * 16 + struct.pack("<ii", 7, -6) + b"\x00" * 10, (7, 6)),
    "webp": (
        b"RIFF\x00\x00\x00\x00WEBPVP8X" + b"\x00" * 8 + (9).to_bytes(3, "little") + (7).to_bytes(3, "little"),
        (10, 8),
    ),
    "webp-lossless": (
        b"RIFF\x00\x00\x00\x00WEBPVP8L\x00\x00\x00\x00\x2f" + ((10 - 1) | ((20 - 1) << 14)).to_bytes(4, "little"),
        (10, 20),
    ),
    "webp-lossy": (b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 10 + struct.pack("<HH", 11, 12), (11, 12)),
    "jpeg": (
        b"\xff\xd8\xff\xe0"
        + struct.pack(">H", 4)
        + b"\x00\x00"
        + b"\xff\xc0"
        + struct.pack(">HBHH", 11, 8, 6, 9)
        + b"\x00" * 6,
        (9, 6),
    ),
}


@pytest.mark.parametrize("kind", list(IMAGES))
def test_image_dimensions(kind: str) -> None:
    """Image dimensions are read from headers."""
    raw, dims = IMAGES[kind]
    assert Images.dimensions(raw) == dims


def test_files_and_images() -> None:
    """Files & images values and Files service responses."""
    raw, _ = IMAGES["png"]
    image = Images.encode_image("Logo", "logo.png", "/img/logo.png", raw, "https://x/logo.png")
    assert image is not None
    assert (image["width"], image["height"], image["size"]) == (3, 2, len(raw))
    assert Images.encode_image("Logo", "logo.png", "/img/logo.png", b"not an image") is None
    assert Images.kind(b"plain") is None
    assert Images.dimensions(b"RIFF\x00\x00\x00\x00WEBPVP8?") is None
    assert Images.dimensions(b"\xff\xd8\x00") is None
    file = Files.encode("Doc", "doc.txt", "/doc.txt", b"abc")
    assert file == {
        "name": "Doc",
        "filename": "doc.txt",
        "path": "/doc.txt",
        "url": None,
        "md5": Files.md5(b"abc"),
        "size": 3,
    }
    assert Files.encode("", "doc.txt", "/doc.txt", b"abc") is None
    assert Files.read("doc.txt", b"abc")["raw"] == base64.b64encode(b"abc").decode()
    assert Files.decode_raw("YWJj") == b"abc"
    assert Files.decode_raw("!!") is None
    assert Files.decode_raw(None) is None


# ====================================================================#
# Fields
# ====================================================================#


def test_field_errors() -> None:
    """Invalid definitions are dropped and reported."""
    factory = FieldsFactory()
    factory.name("No field yet")
    factory.create(FieldType.VARCHAR, "bad id!", "Bad")
    factory.create(FieldType.VARCHAR, "nodesc")
    factory.create("", "notype", "No Type")
    factory.create(FieldType.VARCHAR, "ok", "Ok").add_option("", 1).set_prefer_both()
    field = factory.current()
    assert field is not None
    field.set_sync_mode("sideways")
    assert list(factory.publish()) == ["ok"]
    assert len(factory.errors) == 6
    assert FieldsFactory().publish() == {}


def test_field_alternate_tags() -> None:
    """Alternate tags are filtered and removable."""
    field = ObjectField(FieldType.VARCHAR, "f").set_micro_data("http://schema.org/Thing", "name")
    field.set_alternate_tags(["bad", field.tag or "", "a" * 32, "a" * 32])
    assert field.alternate_tags() == ["a" * 32]
    field.set_alternate_tags([])
    assert "altTags" not in field.options
    field.add_alternate_micro_data("", "x")
    field.set_micro_data("", "")
    assert field.tag is None
    assert field.set_in_list("") is field


def test_factory_options() -> None:
    """Choices without description, write only and list hidden options."""
    factory = FieldsFactory()
    factory.create(FieldType.VARCHAR, "f", "F").add_choices({"low": None, "high": "High"}).is_list_hidden()
    factory.is_write_only(False).is_read_only(False).alternate_tags(["b" * 32]).is_default_language(None)
    published = factory.publish()["f"]
    assert published["choices"] == [{"key": "low", "value": "Low"}, {"key": "high", "value": "High"}]
    assert published["hlist"] is True
    assert published["options"] == {"altTags": '["' + "b" * 32 + '"]'}


# ====================================================================#
# Pipeline
# ====================================================================#


def _groups() -> list[FieldsGroup]:
    """Build groups with dependencies."""

    @fields_group("a", priority=50)
    class A(FieldsGroup):
        pass

    @fields_group("b", priority=10, after=("a",))
    class B(FieldsGroup):
        pass

    @fields_group("c", priority=10, before=("a",))
    class C(FieldsGroup):
        pass

    @fields_group("d", priority=10)
    class D(FieldsGroup):
        pass

    return [A(), B(), C(), D()]


def test_pipeline_is_deterministic() -> None:
    """Any declaration order gives the same pipeline."""
    expected = ["c", "d", "a", "b"]
    for order in permutations(_groups()):
        assert [group.group_code() for group in resolve("X", list(order))] == expected


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"after": ("zz",)}, "unknown group"),
        ({"after": ("b",)}, "cycle"),
        ({"phases": ("never",)}, "invalid phases"),
        ({"phases": ()}, "invalid phases"),
    ],
)
def test_pipeline_errors(changes: dict[str, Any], message: str) -> None:
    """Unknown dependencies, cycles and invalid phases are refused."""
    groups = _groups()
    for key, value in changes.items():
        setattr(groups[0], key, value)
    with pytest.raises(PipelineError, match=message):
        resolve("X", groups)


def test_group_defaults() -> None:
    """A bare group reads and writes nothing, and is named after its class."""
    group = FieldsGroup()
    assert group.group_code() == "FieldsGroup"
    assert group.get(None, "x") is None  # type: ignore[arg-type]
    assert group.set(None, "x", 1) is None  # type: ignore[arg-type]
    assert Phase.DEFAULT == (Phase.POST_CREATE, Phase.UPDATE)


# ====================================================================#
# Widgets Blocks
# ====================================================================#


def test_blocks_factory() -> None:
    """Every block type, options and invalid chart types."""
    blocks = BlocksFactory()
    blocks.set_data("ignored", 1).set_option("ignored", 1)
    blocks.add_text_block("Hello").set_option("AllowHtml", True)
    blocks.add_table_block([["a"]])
    blocks.add_spark_info_block({"title": "T", "value": "1", "other": "x"})
    blocks.add_morris_graph_block([{"x": 1}], "Pie", {"xkey": "x"})
    blocks.add_morris_donut_block([{"x": 1}], {"title": "D"})
    rendered = blocks.render()
    assert [block["type"] for block in rendered] == [
        "TextBlock",
        "TableBlock",
        "SparkInfoBlock",
        "NotificationsBlock",
        "MorrisPieBlock",
        "MorrisDonutBlock",
    ]
    assert rendered[0]["options"]["AllowHtml"] is True
    assert rendered[2]["data"] == {"title": "T", "value": "1"}
    assert rendered[4]["data"] == {"dataset": [{"x": 1}], "xkey": "x"}
