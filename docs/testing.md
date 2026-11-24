# Testing a Connector

splashpy ships a conformance suite: any connector runs it against its own client to check what
Splash expects, without the Splash Toolkit. Install it with `pip install splashpy[testing]`.

## The pytest suite

```python
from splashpy import SplashClient
from splashpy.testing.suite import ConformanceSuite


class TestMyConnector(ConformanceSuite):
    object_types = ("ThirdParty", "Product")      # optional: every object type by default

    @classmethod
    def build_client(cls) -> SplashClient:
        return build_my_client()                   # the client your host application builds
```

Each object type gets its own tests:

| Test             | Checks                                                                          |
|------------------|---------------------------------------------------------------------------------|
| `test_self_test` | the client self test passes, at least one object is exposed                     |
| `test_description` | the object description is complete                                          |
| `test_fields`    | every field definition: keys, identifier, type, lists, primary, metadata tag... |
| `test_pipeline`  | the fields groups order does not depend on their declaration order             |
| `test_crud`      | generated values are created, read back identical, updated, read back, deleted |
| `test_list`      | created objects are listed, `meta` counts them, pagination works               |

Generated values travel through the real wire codec: the connector receives strings, exactly as
from Splash, and its answers are compared by field type (numbers, booleans, prices, dates, inline
lists...). Files, images and links to other objects are not generated: an object with such a
**required** field is skipped for `test_crud` and `test_list`. Values are reproducible
(`seed` class attribute).

The faker runs this suite in `tests/conformance/test_faker_conformance.py`.

## Commits of the host application

Changes made in the host application must be committed to Splash. Check it in the connector own
tests, around a native change:

```python
from splashpy.dictionary import SplOperations
from splashpy.testing import expect_commit

with expect_commit(client, "ThirdParty", SplOperations.UPDATE):
    partner.write({"name": "ACME"})               # native change in the host application
```

## Without pytest

Every check is a function returning the list of problems found, usable from any test runner:
`check_description()`, `check_fields()`, `check_field()`, `check_pipeline()`, `roundtrip()` and
`check_list()` in `splashpy.testing`.

## Splash Toolkit

The conformance suite does not replace the Toolkit validator, which tests the real protocol end
to end (see [Development](development.md)): run both.
