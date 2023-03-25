from __future__ import annotations

import uuid

import ckan.lib.munge as munge

from ckanext.toolbelt.decorators import Collector

NAMESPACE_INGEST = uuid.uuid5(uuid.NAMESPACE_DNS, "ingest")

validator, get_validators = Collector("ingest").split()


@validator
def into_uuid(value):
    return str(uuid.uuid5(NAMESPACE_INGEST, value))


@validator
def munge_name(value):
    return munge.munge_name(value)


@validator
def strip_prefix(prefix):
    def validator(value):
        if isinstance(value, str) and value.startswith(prefix):
            value = value[len(prefix) :]
        return value

    return validator
