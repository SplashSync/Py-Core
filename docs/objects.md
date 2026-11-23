# Objects & Fields Groups

An object type (ThirdParty, Product, Order...) is a `BaseObject` subclass composed of
**fields groups**. Each group declares the fields it owns, reads them and writes them. The
order of groups is **explicit**: it never depends on method names, imports or inheritance.

## Declare an object

```python
from splashpy.fields import FieldsFactory, FieldType
from splashpy.objects import BaseObject, FieldsGroup, ObjectRequest, Phase, fields_group


@fields_group("core", priority=10)
class ProductCore(FieldsGroup):
    def build(self, factory: FieldsFactory, req: ObjectRequest) -> None:
        factory.create(FieldType.VARCHAR, "ref", "Reference").is_required().is_primary().is_listed()
        factory.micro_data("http://schema.org/Product", "model")

    def get(self, req: ObjectRequest, field_id: str):
        return getattr(req.object, field_id)

    def set(self, req: ObjectRequest, field_id: str, value):
        if getattr(req.object, field_id) != value:
            setattr(req.object, field_id, value)
            req.need_update()


@fields_group("prices", after=("core", "currency"))
class ProductPrices(FieldsGroup):
    ...


class Product(BaseObject):
    name = "Product"
    icon = "fa fa-cube"
    groups = (ProductPrices, ProductCore, ProductCurrency)   # order here does not matter

    def load(self, req, object_id): ...           # native object, or None
    def create(self, req): ...                    # create & persist from req.inputs / req.stash
    def object_id(self, req): ...                 # id of req.object
    def update(self, req, needed): ...            # save if needed, return the id
    def delete(self, ctx, object_id): ...         # True, also when already deleted
    def objects_list(self, ctx, filter, params):  # use self.list_result(items, total)
        ...
    def get_by_primary(self, ctx, keys): ...      # optional: id when exactly one match
```

Expose it: `SplashClient(config, objects=[Product])`.

## One package per object

Keep each object in its own package: the object class (identity & CRUD) in `__init__.py`,
one module per part (a fields group with its `build`, `get` and `set`). Parts are included
with `discover_groups()`:

```
objects/product/
├── __init__.py      class Product(BaseObject): CRUD, groups = (*discover_groups(__name__),)
├── core.py          ProductCore: reference, name...
├── prices.py        ProductPrices: after=("core", "currency")
└── variants.py      ProductVariants: phases=(Phase.POST_CREATE, Phase.UPDATE)
```

A part is a fields group class that defines its own `build()`; base classes without fields
are never included. Discovery decides which parts are included, never their order: the order
always comes from `after` / `before` / `priority`. The faker (`splashpy/faker/objects/`) is
organized this way.

## Pipeline order

Resolved once, when the client is built:

1. topological sort on `after` / `before` dependencies;
2. then `priority` (lower runs earlier);
3. then `code`, so the order is deterministic.

These are **startup errors**, never sync-time bugs: a dependency cycle, an unknown
dependency, a duplicated group code, a field defined by two groups, a list shared by two groups,
or an object without fields.

`splashpy describe --order` prints the resolved pipeline of every object:

```
simple (faker)
  1. core           priority=10              phases=post_create,update  fields: name
  2. basic          priority=20 after=core   phases=post_create,update  fields: text, bool, int, double...
  3. advanced       priority=30 after=basic  phases=post_create,update  fields: lang, country, price, tags...
  4. translations   priority=40 after=basic  phases=post_create,update  fields: title, title_fr_FR
```

## Field ownership

Each field id belongs to the group that created it in `build()`. Reads and writes are routed
to the owner: a group only receives its own fields. A requested field without an owner fails
the request with an explicit error.

## Write phases

| Phase         | When                                    | `req.object`                  |
|---------------|-----------------------------------------|-------------------------------|
| `create`      | before `create()`, new objects only     | None: keep values in `req.stash` |
| `post_create` | right after `create()`                  | the new object (id known)     |
| `update`      | existing objects                        | the loaded object             |

Default phases: `post_create` and `update`. A `Set` runs the groups of its phases in pipeline
order, then calls `update(req, needed=req.is_to_update())`.

## Values

- Values received from Splash are **strings** (`"1"` / `"0"` for booleans); `""` becomes None.
- Lists: a group owning `sku@lines` and `qty@lines` receives the whole `lines` list on write
  (a list of dicts) and returns one value per item on read.
- Values stay as received: the connector converts them when it uses them.

### Helpers

All in `splashpy.fields`, one module per helper in `splashpy/fields/helpers/`:

| Helper       | Use                                                                         |
|--------------|-----------------------------------------------------------------------------|
| `Prices`     | build, validate, compare prices, read an amount (also from received strings) |
| `Files`      | build a file value, answer `ReadFile`, decode received contents             |
| `Images`     | same as `Files`, plus image type and size read from headers                 |
| `ObjectIds`  | build and split object links `id::Type`                                     |
| `Lists`      | build and split list field ids `field@list`                                 |
| `Inline`     | convert inline values from / to Python lists                                |
| `Dates`      | format and parse Splash dates and datetimes                                 |
| `Validators` | check basic values: email, url, phone, country, state, lang, currency, dates |

Validators only answer True or False, never convert nor fix a value: the connector decides
what to do with an invalid one.

```python
from splashpy.fields import Validators

if not Validators.is_email(value):
    req.logger.warning(f"Invalid email: {value}")
```

## Locks & commits

While Splash writes an object, the object is locked (`new` during creation, then its id), so
changes made meanwhile by the host application are not sent back:

```python
client.commit("Product", product.id, SplOperations.UPDATE, user="admin")
```

A commit is skipped (and recorded in `client.commits`) when the type is unknown, the object
is locked or filtered by an extension, or in CI mode (`SPLASH_CI` / `SPLASH_TRAVIS`).
