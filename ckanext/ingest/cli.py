import click
import json
import logging

from ckan.lib.redis import connect_to_redis

from . import utils

logger = logging.getLogger(__name__)


def get_commnads():
    return [ingest]


@click.group()
def ingest():
    pass


@ingest.command()
@click.argument(u"ingest_name", required=True)
def process(ingest_name):
    try:
        name = ingest_name
    except IndexError:
        print("You must provide name of the queue to remove")
        return
    ingester = utils.get_ingestier(name)
    if ingester is None:
        print("No queue processors registered for <{}>".format(name))
        return
    conn = connect_to_redis()
    size = conn.llen("ckanext:ingest:queue:" + name)
    i = 0
    while True:
        record = conn.lpop("ckanext:ingest:queue:" + name)
        if not record:
            break
        i += 1
        print("Processing {:>{}} of {}".format(i, len(str(size)), size))

        ingester.process(json.loads(record))
    print("Done")


@ingest.command()
@click.argument(u"ingest_name", required=True)
def drop_queue(ingest_name):
    try:
        name = ingest_name
    except IndexError:
        print("You must provide name of the queue to remove")
        return

    conn = connect_to_redis()
    conn.delete("ckanext:ingest:queue:{}".format(name))
    print("Done.")


@ingest.command()
def list_queues():
    conn = connect_to_redis()
    keys = conn.keys("ckanext:ingest:queue:*")
    print("Available queues:")
    for key in keys:
        print(
            "\t{}\n\t\tSize: {:>6}. Expires in {}s".format(
                str(key).split(":")[-1], conn.llen(key), conn.ttl(key)
            )
        )
