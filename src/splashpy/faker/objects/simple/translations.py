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

"""simple: translated fields."""

from __future__ import annotations

from typing import Any, Final

from splashpy.faker.objects.base import StoredGroup
from splashpy.fields import FieldsFactory, FieldType
from splashpy.objects import ObjectRequest, fields_group

GROUP: Final = "Translations"
"""Fields group label."""

LANGUAGES: Final = ("en_US", "fr_FR")
"""Languages, the first is the default one (it keeps the plain field id)."""


@fields_group("translations", priority=40, after=("basic",))
class SimpleTranslations(StoredGroup):
    """A title in every language."""

    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        """Declare translated fields."""
        factory.set_default_language(LANGUAGES[0])
        for iso_code in LANGUAGES:
            factory.create(FieldType.VARCHAR, "title", f"Title ({iso_code})").group(GROUP)
            factory.micro_data("http://schema.org/Product", "alternateName").set_multi_lang(iso_code)

    def get(self, req: ObjectRequest, field_id: str) -> Any:
        """Read a translation."""
        return self.read(req, field_id)

    def set(self, req: ObjectRequest, field_id: str, value: Any) -> bool | None:
        """Write a translation."""
        return self.write(req, field_id, value)
