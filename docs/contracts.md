# Contracts: Field Templates & Scopes

Splash publishes standard field definitions (**templates**) and connector contracts (**scopes**)
in a catalog compiled by Php-Scopes. splashpy uses the same catalog as Php-Core: a field built
from a template is published exactly like Php-Core publishes it.

## Field templates

A template gives the type, the schema.org metadata, flags, choices, options, a name and a
description (translated). Never write microdata by hand when a template exists.

```python
from splashpy.fields import FieldsFactory

factory.create_from_template("email", "Splash.Templates.ThirdParty.Core.Email")
factory.create_from_template("civility", "Splash.Templates.ThirdParty.Profile.CivilityType", "Title")
factory.create(FieldType.VARCHAR, "zip").template("Splash.Templates.Address.PostalAddress.PostalCode")
factory.is_required()                      # everything can still be overridden after the template
```

- Names and descriptions use the factory default language (`set_default_language()`), English
  otherwise.
- The template code is published in the `tmpl` option of the field.
- An unknown template code is an error when the client is built, never at sync time.

## Scopes

A scope lists the fields a server commits to expose for an object type. The Splash validator
checks it. Declare scopes in the client information:

```python
from dataclasses import replace
from splashpy import ClientInfo

info = replace(ClientInfo(), scopes=["Splash.Scopes.ThirdParty.Provider"])
client = SplashClient(config, info=info, objects=[ThirdParty])
```

Extensions may add scopes from their `client_info()` hook. An unknown scope code is a
configuration error when the client is built.

## The catalog

The catalog is **embedded in the package**: templates and scopes always work, offline included,
without any download.

| Command                              | Effect                                                           |
|--------------------------------------|------------------------------------------------------------------|
| `splashpy contracts show`            | Show the catalog in use: origin, version, commit                 |
| `splashpy contracts update`          | Download the latest catalog into the cache, when it differs      |

- `update` first downloads the catalog index only. When its commit is the one of the catalog in
  use (cache or embedded), nothing else is downloaded and nothing is written.
- The cache (`~/.cache/splashpy/contracts`, `SPLASH_CONTRACTS_CACHE` to change it) is only used
  when it is complete, valid and newer than the embedded catalog. An invalid cache is ignored with
  a warning, an older one silently (after an upgrade of splashpy, for instance).
- Nothing is ever downloaded while serving Splash requests.
- Downloads are checked: supported format, SHA-256 of each file against the catalog index. An
  invalid download never replaces the current catalog.
- Hosts with their own storage plug a cache: any object with `read(name)` and `write(name, raw)`,
  given to `ContractsProvider(cache)`.

Source: `https://gitlab.com/api/v4/projects/SplashTools%2Fscopes/packages/generic/catalog/latest/`
(`index.json`, `templates.json`, `scopes.json`). `make contracts` refreshes the embedded copy.
