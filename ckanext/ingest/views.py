# -*- coding: utf-8 -*-

import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h

from flask import Blueprint
from flask.views import MethodView

from . import utils


def get_blueprints():
    path = utils.get_index_path()
    bp = Blueprint(u"ingest", __name__)
    bp.add_url_rule(path, "index", IngestView.as_view("index"))
    return bp


class IngestView(MethodView):
    def get(self, *args, **kwargs):
        data = {
            "base_template": utils.get_base_template(),
            "ingestion_formats": utils.get_ingestiers(),
        }
        return tk.render(utils.get_main_template(), data)

    def post(self, *args, **kwargs):
        r = tk.request
        fmt = r.form.get("format")
        source = r.files.get("source")
        if not fmt or not source:
            h.flash_error("Either format or source is missing.")
            return tk.redirect_to("ingest.index", *args, **kwargs)

        ingester = utils.get_ingestier(fmt)
        if not ingester:
            h.flash_error(
                "There is no registered extractor for [{}] format.".format(fmt)
            )
            return tk.redirect_to("ingest.index", *args, **kwargs)
        records = ingester.extract(source)
        try:
            for record in records:
                utils.store_record(record, fmt)
        except utils.StoreException as e:
            h.flash_error("Error: {}.".format(e))
        else:
            h.flash_success("Ingestion finished.")
        return tk.redirect_to("ingest.index", *args, **kwargs)
