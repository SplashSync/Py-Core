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

"""Fields groups discovery: one object package, one module per part.

An object can keep each part (fields group) in its own module, inside the object
package, and include them all with::

    groups = discover_groups(__name__)

A part is a fields group class that defines its own ``build()`` in that module: base
classes without fields (or names starting with ``_``) are never included.

Discovery only decides WHICH groups are included; their ORDER stays explicit
(``after`` / ``before`` / ``priority``), resolved by the pipeline.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from splashpy.objects.group import FieldsGroup


def discover_groups(package: str) -> tuple[type[FieldsGroup], ...]:
    """Collect the fields groups defined in the modules of a package (not in sub packages).

    :param package: dotted name of the package, usually ``__name__`` of the object package.
    :raises ValueError: when the name is not a package.
    """
    module = importlib.import_module(package)
    paths = getattr(module, "__path__", None)
    if paths is None:
        raise ValueError(f"{package} is not a package: fields groups cannot be discovered.")
    found: list[type[FieldsGroup]] = []
    for info in sorted(pkgutil.iter_modules(paths), key=lambda item: item.name):
        if info.ispkg:
            continue
        submodule = importlib.import_module(f"{package}.{info.name}")
        for candidate in vars(submodule).values():
            if (
                inspect.isclass(candidate)
                and issubclass(candidate, FieldsGroup)
                and candidate.__module__ == submodule.__name__
                and "build" in vars(candidate)
                and not candidate.__name__.startswith("_")
            ):
                found.append(candidate)
    return tuple(found)
