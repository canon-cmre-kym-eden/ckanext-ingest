from __future__ import annotations

from flask import Blueprint
from flask.views import MethodView

import ckan.plugins.toolkit as tk
import ckan.lib.base as base

from . import utils

ingest = Blueprint("ingest", __name__)

def get_blueprints():

    return [ingest]


class IngestView(MethodView):
    def _check_access(self):
        try:
            tk.check_access("ingest_web_ui", {"user": tk.g.user})
        except tk.NotAuthorized:
            tk.abort(401, tk._("Unauthorized to ingest data"))

    def _render(self, errors=None):
        data = {"user_dict": tk.g.userobj, "errors": errors,
                "base_template": utils.get_base_template(),
                }
        return base.render("ingest/index.html", extra_vars=data)

    def get(self):
        self._check_access()
        return self._render()

    def post(self):
        self._check_access()
        errors = {}
        try:
            data = dict(tk.request.form)
            data.update(tk.request.files)
            result = tk.get_action("ingest_import_datasets")({}, data)
        except tk.ValidationError as e:
            errors = e.error_summary

        return self._render(errors)



ingest.add_url_rule("/ingest/from-source", view_func=IngestView.as_view("index"))
