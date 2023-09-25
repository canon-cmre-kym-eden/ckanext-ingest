[![Tests](https://github.com/DataShades/ckanext-ingest/workflows/Tests/badge.svg)](https://github.com/DataShades/ckanext-ingest/actions/workflows/test.yml)

# ckanext-ingest

Framework for data import from arbitrary sources.

Note: this extension has no aim to perform import of every possible data source
into CKAN. Instead, it defines a structure and rules for making import more
predictable, reusable and flexible.

This extension can be used if you need to:

* ingest a lot of different files in order to create
  datasets/resources/etc. But you want do import all files in a similar manner
  and don't want to spend time introducing and explaining the whole process.
* reuse ingestion logic in different projects
* share pieces of logic between different ingestion workflows

And you probably don't need it if you want to:

* import a single file using CLI and never use this code again.


## Structure

* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)
* [Examples](#examples)
* [Advanced](#advanced)
* [Configuration](#configuration)
* [Interfaces](#interfaces)
* [API](#api)
  * [`ingest_extract_records`](#ingest_extract_records)
  * [`ingest_import_records`](#ingest_import_records)

## Requirements

Compatibility with core CKAN versions:

| CKAN version | Compatible? |
|--------------|-------------|
| 2.9          | no          |
| 2.10         | yes         |
| master       | yes         |


## Installation

To install ckanext-ingest:

1. Install it via **pip**:
   ```sh
   pip install ckanext-ingest

   ## with basic XLSX strategy
   # pip install 'ckanext-ingest[xlsx]'
   ```
1. Add `ingest` to the `ckan.plugins` setting in your CKAN config file.

## Usage

Data can be ingested into CKAN via `ingest_import_records` API action. It
requires a `source` with the data, and it's recommended to pass an extraction
`strategy`, to get a full control over the process.

```sh
ckanapi action ingest_import_records source@path/to/data.zip strategy="myext:extract_archive"
```

But before anything can be ingested you have to regiser a `strategy` that
produces `records`. `strategy` defines how source is parsed, and `record`
represent minimal amount of data from the source that is required for
**ingestion**(process when something is created/updated/etc.).

`strategy` is registered via `IIngest` interface. It has to be a subclass of
`ckanext.ingest.shared.ExtractionStrategy`. The only requirement for
`strategy` is to return iterable of `records` from its `extract` method.

`record` is created by `strategy` and it has to be a subclass of
`ckanext.ingest.shared.Record`. Its `ingest` method is responsible for
ingestion: depending on the record purpose, it can create/update/delete data or
perform any other task that has sense.


## Examples

### Register custom strategy

```python

import ckan.plugins as p

from ckanext.ingest.interfaces import IIngest

class MyPlugin(p.SingletonPlugin):
    p.implements(IIngest)

    def get_ingest_strategies(self):
        return {
          "my:custom_strategy": CustomStrategy
        }

```

### JSON with the data for a single dataset
```python
import ckan.plugins.toolkit as tk
from ckanext.ingest.shared import ExtractionStrategy, Storage, Record, IngestionResult

class SingleJsonStrategy(ExtractionStrategy):

    def extract(self, source: Storage, options):
        # source is a readable IO stream(werkzeug.datastructures.FileStorage)
        data = json.load(source)

        # `extract` returns iterable over records. When the strategy produces
        # a single record, this record can be either yielded or returned as
        # a list with a single element
        yield SimplePackageRecord(data, {})

class SimplePackageRecord(Record):
    def ingest(self, context: ckan.types.Context) -> IngestionResult:

        dataset = tk.get_action("package_create")(context, self.data)

        # `ingest` returns a brief overvies of the ingestion
        return {
            "success": True,
            "result": dataset,
            "details": {}
        }

```

### CSV with a list of organizations that require removal

```python
import csv
import ckan.plugins.toolkit as tk
from ckanext.ingest.shared import ExtractionStrategy, Record

class DropOrganizationsUsingCsvStrategy(ExtractionStrategy):

    def extract(self, source, options):
        # `source` is an `IO[bytes]`, so we turn in into `IO[str]`
        str_stream = StringIO(source.read().decode())
        rows = csv.DictReader(st_stream)

        for row in rows:
            # record's constructor requires two arguments:
            # the raw data and the mapping with record options.
            yield DropOrganiationRecord(row, {})

class DropOrganizationRecord(Record):
    def ingest(self, context: ckan.types.Context):
        try:
            tk.get_action("organization_delete")(context, {"id": self.data["name"]})
        except tk.ObjectNotFound:
            success = False
        else:
            success = True

        return {
            "success": success,
            "result": None,
            "details": {}
        }

```

### Pull datasets from CKAN instance specified in JSON, and remove datasets that were not modified by this ingestion.

```python
import json
from datetime import datetime
from ckanapi import RemoteCKAN
import ckan.plugins.toolkit as tk
from ckanext.ingest.shared import ExtractionStrategy, Record

class HarvestStrategy(ExtractionStrategy):

    def extract(self, source, options):
        details = json.load(source)
        client = RemoteCKAN(**details)

        now = datetime.utcnow()

        # produce a record that creates a package for every remote dataset
        for dataset in client.action.package_search()["results"]:
            yield SimpleDatasetRecord(row, {})

        # produce an additional record that removes stale datasets
        yield DeleteStaleDatasetsRecord({"before": now}, {})

class SimplePackageRecord(Record):
    def ingest(self, context: ckan.types.Context) -> IngestionResult:

        dataset = tk.get_action("package_create")(context, self.data)

        return {
            "success": True,
            "result": dataset,
            "details": {"remote_id": self.data["id"]}
        }


class DeleteStaleDatasetsRecord(Record):
    def ingest(self, context: ckan.types.Context) -> IngestionResult:
        before = self.data["before"].isoformat()
        result = tk.get_action("package_search")(
            context,
            {"fq": f"metadata_modified:[* TO {before}]", "fl": "id"}
        )

        deleted = []
        for dataset in result["results"]
            tk.get_action("package_delete")(context, {"id": dataset["id"]})
            deleted.append(id)

        return {
            "success": True,
            "result": deleted,
            "details": {"count": len(deleted), "before": before}
        }


```

## Advanced

To get the most from ingestion workflows, you can make strategies and records
reusable. Details below will help you in achieving this.

### Strategy autodetection

`strategy` argument for actions is optional. When it missing, the plugins will
choose the most suitable strategy for the ingested source. This feature relies
on `can_handle` and `must_handle` methods of the extraction strategy. Both
methods receive the mimetype of the source and the source itself and return
`True`/`False`.

Amont all strategies that return `True` from `can_handle`, plugin will choose
the first that returns `True` from `must_handle`. If there is no such strategy,
the first `can_handle` wins.

`ckanext.ingest.shared.ExtractionStrategy` defines both these
methods. `must_handle` always returns `False`. `can_handle` return `True` if
source's mimetype is listed in `mimetypes` property of the handler:

```python
class ExtractionStrategy:
    mimetypes: ClassVar[set[str]] = set()

    @classmethod
    def can_handle(cls, mime: str | None, source) -> bool:
        return mime in cls.mimetypes

    @classmethod
    def must_handle(cls, mime, source) -> bool:
        return False

```

If you want to register strategy that can handle JSON sources, just register
strategy with an appropriate `mimetypes`:

```python
class JsonStrategy(ExtractionStrategy):
    mimetypes = {"application/json"}
```

If you want to register strategy always handles JSON sources if the filename of
ingested source is `DRINK_ME.json`, you can use `must_handle`. Note, that
`must_handle` is checked only when `can_handle` returns `True`, so we still
using default `mimetypes` logic and not moving everything inside `must_handle`:

```python
class DrinkMeJsonStrategy(ExtractionStrategy):
    mimetypes = {"application/json"}

    @classmethod
    def must_handle(cls, mime, source: Storage) -> bool:
        return source.filename == "DRINK_ME.json"
```

### Record factories

`ExtractionStrategy` has a default implementation of `extract`. This default
implementation calls `chunks` method to parse the source and get ingestable
data fragments. Then, for every data chunk `chunk_into_record` method is
called, to transform arbitrary data into a `Record`. Finally, `extract` yields
whatever is produced by `chunk_into_record`.

Default implementation of `chunks` ignores the source and returns an empty
list. The first thing you can do to produce a data is overriding `chunks`.

If you are working with CSV file, `chunks` can return rows from this file:

```python
class CsvRowsStrategy(ExtractionStrategy):
    mimetypes = {"text/csv"}

    def chunks(self, source, options) -> Iterable[Any]:
        str_stream = StringIO(source.read().decode())
        rows = csv.reader(str_stream)

        yield from rows
```

Such strategy will produce `ckanext.ingest.shared.Record` for every row of the
source CSV. But base `Record` class doesn't do much, so you need to replace it
with your own `Record` subclass.

As mentioned before, data chunk converted into a record via `chunk_into_record`
method. You can either override it, or use default implemmentation, which
creates instances of the class stored under `record_factory` attribute of the
strategy. Default value of this attribute is `Record` and if you want to use a
different record implementation, do the following:

```python
class CsvRowsStrategy(ExtractionStrategy):
    record_factory = MyCustomRecord
    ...
```

## Configuration

```ini
# List of allowed ingestion strategies. If empty, all registered strategies
# are allowed
# (optional, default: )
ckanext.ingest.strategy.allowed = ingest:recursive_zip

# List of disabled ingestion strategies.
# (optional, default: )
ckanext.ingest.strategy.disabled = ingest:scheming_csv

# Base template for WebUI
# (optional, default: page.html)
ckanext.ingest.base_template = admin/index.html

# Allow moving existing resources between packages.
# (optional, default: false)
ckanext.ingest.allow_resource_transfer = true

# Rename strategies using `{"import.path.of:StrategyClass": "new_name"}` JSON
# object
# (optional, default: )
ckanext.ingest.strategy.name_mapping = {"ckanext.ingest.strategy.zip:ZipStrategy": "zip"}
```

## Interfaces

`ckanext.ingest.interfaces.IIngest` interface implementations can regiser
custom extraction strategies via `get_ingest_strategies` method::

```python
def get_ingest_strategies() -> dict[str, type[ckanext.ingest.shared.ExtractionStrategy]]:
    """Return extraction strategies."""
    return {
        "my_plugin:xlsx_datasets": MyXlsxStrategy,
    }
```

## API

### `ingest_extract_records`

Extract records from the source.

This method mainly exists for debugging. It doesn't create anything, just
parses the source, produces records and return record's data as a
list. Because it aggregates all extracted records into a single list, it
can consume a lot of memory. If you want to iterate over, consider using
`iter_records` function that produces an iterable over records.

Args:

    source: str|FileStorage - data source for records

    strategy: str|None - record extraction strategy. If missing, strategy
    is guessed depending on source's mimetype

    options: SourceOptions - dictionary with configuration for strategy and
    records. Consumed by strategies so heavily depends on the chosen
    strategy.


### `ingest_import_records`

Ingest records extracted from source.

Parse the source, convert it into Records using selected strategy, and call
`Record.ingest`, potentially creating/updating data.

Args:

    source: str|FileStorage - data source for records

    strategy: str|None - record extraction strategy. If missing, strategy
    is guessed depending on source's mimetype

    options: SourceOptions - dictionary with configuration for strategy and
    records. Consumed by strategies so heavily depends on the chosen
    strategy.

    defaults: dict[str, Any] - default data added to every record(if missing)

    overrides: dict[str, Any] - data that unconditionally overrides record details

    skip: int - number of records that are skipped without ingestion

    take: int - max number of records that will be ingested
