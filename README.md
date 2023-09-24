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

* [Usage](#usage)
* [Examples](#examples)
* [Requirements](#requirements)
* [Installation](#installation)
* [Configuration](#configuration)
* [Interfaces](#interfaces)
* [API](#api)
  * [`ingest_extract_records`](#ingest_extract_records)
  * [`ingest_import_records`](#ingest_import_records)

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
`ckanext.ingest.shared.ExtractionStrategy` class. The only requirement for
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

        # extract must return iterable over records. When the strategy produces
        # a single record, it can be either yielded or returned as a list with
        # a single element
        yield SimplePackageRecord(data, {})

class SimplePackageRecord(Record):
    def ingest(self, context: ckan.types.Context) -> IngestionResult:

        dataset = tk.get_action("package_create")(context, self.data)

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
        rows = csv.DictReader(StringIO(source.read().decode()))

        for row in rows:
            if row["name"]:
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

        for dataset in client.action.package_search()["results"]:
            yield SimpleDatasetRecord(row, {})

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
