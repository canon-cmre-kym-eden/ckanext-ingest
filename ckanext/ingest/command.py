import json
import logging
import os

import ckan.model as model
from ckan.lib.redis import connect_to_redis
import ckan.plugins.toolkit as toolkit
import paste.script

from ckan.common import config
from ckan.lib.cli import CkanCommand
import ckan.lib.search as search
from ckanext.ingest.plugin import get_ingestier

logger = logging.getLogger(__name__)


class IngestCommand(CkanCommand):
    """
    ckanext-ingest management commands.

    Usage::
    paster ingest [command]

    Commands::
        process QUEUE    create data using records from QUEUE.
        list-queues      show all available queues for data processing.
        drop-queue QUEUE delete whole queue without processing records.
    ...
    """

    summary = __doc__.split('\n')[0]
    usage = __doc__

    # parser = paste.script.command.Command.standard_parser(verbose=True)
    # parser.add_option(
    #     '-c',
    #     '--config',
    #     dest='config',
    #     default='../spc.ini',
    #     help='Config file to use.'
    # )

    def command(self):
        self._load_config()

        cmd_name = (self.args[0] if self.args else '').replace('-', '_')
        cmd = getattr(self, cmd_name, None)
        if cmd is None:
            return self.usage

        return cmd()

    def process(self):
        try:
            name = self.args[1]
        except IndexError:
            print('You must provide name of the queue to remove')
            return
        ingester = get_ingestier(name)
        if ingester is None:
            print('No queue processors registered for <{}>'.format(name))
            return
        conn = connect_to_redis()
        size = conn.llen('ckanext:ingest:queue:' + name)
        i = 0
        while True:
            record = conn.lpop('ckanext:ingest:queue:' + name)
            if not record:
                break
            i += 1
            print('Processing {:>{}} of {}'.format(i, len(str(size)), size))

            ingester.process(json.loads(record))
        print('Done')

    def drop_queue(self):
        try:
            name = self.args[1]
        except IndexError:
            print('You must provide name of the queue to remove')
            return

        conn = connect_to_redis()
        conn.delete('ckanext:ingest:queue:{}'.format(name))
        print('Done.')

    def list_queues(self):
        conn = connect_to_redis()
        keys = conn.keys('ckanext:ingest:queue:*')
        print('Available queues:')
        for key in keys:
            print(
                '\t{}\n\t\tSize: {:>6}. Expires in {}s'.format(
                    key.split(':')[-1], conn.llen(key), conn.ttl(key)
                )
            )
