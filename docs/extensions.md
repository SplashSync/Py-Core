# Extensions & Widgets

## Extensions

An `Extension` adds features to a client without changing its code: objects, fields groups for
existing objects, filters, configurators, widgets, client information and event listeners.

```python
from splashpy import Extension


class SupplierExtension(Extension):
    name = "suppliers"

    def fields_groups(self):
        return {"Product": (ProductSupplier,)}       # joins the Product pipeline, e.g. after=("prices",)

    def is_filtered(self, ctx, object_type, object_id, obj):
        return False                                   # True hides the object (reads & commits)

    def configure_fields(self, ctx, object_type, fields):
        fields.pop("internal_code", None)              # override published definitions

    def on_commit(self, ctx, event):
        ...                                            # event.sent tells if it was sent
```

| Hook                    | Use                                                        |
|-------------------------|------------------------------------------------------------|
| `objects()`             | extra objects (highest `priority` wins a type; equal = error) |
| `fields_groups()`       | groups added to existing objects, ordered with core groups |
| `widgets()`             | extra widgets                                              |
| `client_info()`         | complete client information                                |
| `is_filtered()`         | hide objects from reads and commits                        |
| `configure_description()`, `configure_fields()` | override definitions       |
| `before_set()`, `after_set()`, `on_commit()`    | events (failures are logged, never break the request) |

### Enabling extensions

Nothing is enabled implicitly.

- **Explicitly** (hosts whose add-ons are not pip packages, e.g. Odoo):
  `SplashClient(config, extensions=[SupplierExtension()])`.
- **Installed packages** declare an entry point:

  ```toml
  [project.entry-points."splash"]
  suppliers = "my_package:SupplierExtension"
  ```

  and are enabled by name in the client configuration: `extensions = ["suppliers"]`
  (`SPLASH_EXTENSIONS=suppliers`). An unknown name is a configuration error.

## Widgets

```python
from splashpy.widgets import BaseWidget, WidgetSize


class SalesWidget(BaseWidget):
    name = "Sales"
    icon = "fa fa-chart-line"
    options = {"Width": WidgetSize.L}

    def render(self, ctx, params, output):
        output.set_sub_title("Last 7 days")
        output.blocks.add_morris_graph_block(dataset, "Bar", {"xkey": "day", "ykeys": ["total"]})
        return True                                    # False fails the request
```

Expose them with `SplashClient(config, widgets=[SalesWidget])` or from an extension. Each call
renders a new output: nothing is shared between widgets, calls or threads.

Blocks: text, notifications, table, spark info, Morris bar / area / line / donut charts.

## Faker

`splashpy.faker.FakerExtension` is a demo connector used by the E2E tests, aligned on the
Php-Core faker types:

| Type      | Content                                                                         |
|-----------|---------------------------------------------------------------------------------|
| `short`   | a varchar and a bool, only to check the synchronization works                   |
| `simple`  | every field type but images & files: basic, advanced (price, inlines with and without choices, link to `short`) and translated fields |
| `list`    | a list of basic types: bool, varchar, double, price                             |
| `primary` | the only object with a primary key                                              |
| `image`   | two images                                                                      |
| `file`    | one file                                                                        |

Plus two widgets. It is for development and tests only: enable it with
`splashpy serve --faker` or by name (`faker`), never in production.

### Faker files

Files and images received by the faker are really downloaded, like a real connector would:

1. the received value gives a path and a checksum: the faker asks Splash for the file
   (`ReadFile`, `client.get_file()` / `ctx.get_file()`) and checks its md5;
2. the raw file is stored once, by checksum, in the `files` table, with its size, mime type
   and image dimensions. The same contents received under another name are not stored twice;
3. objects only keep the name, the filename and the checksum. Read values are rebuilt from
   the stored file (path, size, dimensions), never from what was received.

Stored files are published:

| To     | How                                                                     |
|--------|-------------------------------------------------------------------------|
| Splash | `ReadFile` with path `faker/files/<md5>` and the checksum               |
| Humans | `GET <server path>/files/<md5>`, the `url` of read values (`splashpy serve --faker`) |
