# -*- coding: utf-8 -*-

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h

from flask import Blueprint
from flask.views import MethodView
from ckanext.ingest.cli import get_commnads

from . import (
    get_index_path, get_base_template, get_main_template, get_ingestiers,
    get_ingestier, store_record,
    StoreException
)


class IngestView(MethodView):

    def get(self, *args, **kwargs):
        data = {
            "base_template": get_base_template(),
            "ingestion_formats": get_ingestiers(),
        }
        return toolkit.render(get_main_template(), data)

    def post(self, *args, **kwargs):
        r = toolkit.request
        fmt = r.form.get('format')
        source = r.files.get('source')
        if not fmt or not source:
            h.flash_error('Either format or source is missing.')
            return toolkit.redirect_to('ingest.index', *args, **kwargs)

        ingester = get_ingestier(fmt)
        if not ingester:
            h.flash_error(
                'There is no registered extractor for [{}] format.'.
                format(fmt)
            )
            return toolkit.redirect_to('ingest.index', *args, **kwargs)
        records = ingester.extract(source)
        try:
            for record in records:
                store_record(record, fmt)
        except StoreException as e:
            h.flash_error('Error: {}.'.format(e))
        else:
            h.flash_success('Ingestion finished.')
        return toolkit.redirect_to('ingest.index', *args, **kwargs)


class IngestFlaskPlugin(plugins.SingletonPlugin):
    u'''Flask-specific implementation'''

    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)

    # IBlueprint

    def get_blueprint(self):
        path = get_index_path()
        bp = Blueprint(u'ingest', self.__module__)
        bp.add_url_rule(path, 'index', IngestView.as_view('index'))
        return bp

    # IClick
    def get_commands(self):
        return get_commnads()
