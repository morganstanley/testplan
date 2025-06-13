#!/usr/bin/env python
"""
Web application for Testplan & Monitor UIs,
"""

import os
import pathlib
import argparse
from threading import Thread

import orjson

try:
    import werkzeug.exceptions
    from cheroot.wsgi import Server as WSGIServer, PathInfoDispatcher
    from flask import Flask, send_from_directory, redirect, jsonify
    from flask_orjson import OrjsonProvider
    from flask_restx import Resource, Api
except ImportError as e:
    raise RuntimeError(
        "Certain packages failed to import, please consider installing Testplan "
        "package with `interactive` extra to use this feature."
    ) from e

from testplan import defaults
from testplan.common.utils.path import pwd
from .fix_spec import FIX_SPEC

TESTPLAN_UI_STATIC_DIR = os.path.abspath(os.path.dirname(__file__))
INDEX_HTML = "index.html"
TESTPLAN_REPORT = os.path.basename(defaults.JSON_PATH)
MONITOR_REPORT = "monitor_report.json"

app = Flask(__name__)
_provider = OrjsonProvider(app)
_provider.option |= orjson.OPT_NON_STR_KEYS
app.json = _provider
_api = Api(app)


def parse_cli_args():
    """Web App command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--static-path", nargs="?", default=None, const=pwd())
    parser.add_argument("--data-path", nargs="?", default=None, const=pwd())
    parser.add_argument("--report-name", nargs="?", default=None, const=pwd())
    return parser.parse_args()


@app.route("/")
@app.route("/testplan/")
def redirect_to_landing():
    return redirect("/testplan/local", code=301)


@_api.route("/testplan/<path:selection>")
class Testplan(Resource):
    def get(self, selection=None):
        """Get a Testplan report (HTML) given it's uid."""
        directory = os.path.abspath(
            os.path.join(app.config["STATIC_PATH"], "testing", "build")
        )
        index_path = os.path.join(directory, INDEX_HTML)

        if os.path.exists(index_path):
            return send_from_directory(directory=directory, path=INDEX_HTML)
        else:
            raise werkzeug.exceptions.NotFound()


@_api.route("/api/v1/reports/<string:report_uid>")
class TestplanReport(Resource):
    def get(self, report_uid):
        """Get a Testplan report (JSON) given it's uid."""
        # report_uid will be used when looking up the report from a database.
        report_path = os.path.abspath(
            os.path.join(
                app.config["DATA_PATH"], app.config["TESTPLAN_REPORT_NAME"]
            )
        )

        if os.path.exists(report_path):
            return send_from_directory(
                directory=os.path.dirname(report_path),
                path=os.path.basename(report_path),
            )
        else:
            raise werkzeug.exceptions.NotFound()


@_api.route(
    "/api/v1/reports/<string:report_uid>/assertions/<string:assertions_uid>"
)
class TestplanAssertions(Resource):
    def get(self, report_uid, assertions_uid):
        """
        Get an Assertion report (JSON) for a specific Testplan report given
        their uids.
        """
        raise werkzeug.exceptions.NotImplemented()  # pylint: disable=notimplemented-raised


@_api.route(
    "/api/v1/reports/<string:report_uid>/attachments/<path:attachment_path>"
)
class TestplanAttachment(Resource):
    def get(self, report_uid, attachment_path):
        """Get an attachment for a specific Testplan report given their uids."""
        base_path = (
            pathlib.Path(app.config["DATA_PATH"]) / defaults.ATTACHMENTS
        ).resolve()

        # security check for argument from url
        if not str((base_path / attachment_path).resolve()).startswith(
            str(base_path)
        ):
            raise werkzeug.exceptions.NotFound()

        full_attachment_path = base_path / attachment_path
        if not full_attachment_path.is_file():
            raise werkzeug.exceptions.NotFound()

        return send_from_directory(
            directory=full_attachment_path.parent,
            path=full_attachment_path.name,
        )


@_api.route("/api/v1/testplan_monitor/<string:resource_id>")
class TestplanResource(Resource):
    def get(self, resource_id):
        """Get a Testplan resource (JSON) given it's uid."""
        # resource_id will be used when looking up the report from a database.
        base_path = (
            pathlib.Path(app.config["DATA_PATH"]) / defaults.RESOURCE_DATA
        ).resolve()
        if (base_path / defaults.RESOURCE_META_FILE_NAME).exists():
            return send_from_directory(
                directory=base_path, path=defaults.RESOURCE_META_FILE_NAME
            )
        else:
            raise werkzeug.exceptions.NotFound()


@_api.route(
    "/api/v1/testplan_monitor/<string:resource_id>/attachments/<path:attachment_path>"
)
class TestplanResourceAttachment(Resource):
    """Get an attachment for a specific Testplan resource given their uids."""

    def get(self, resource_id, attachment_path):
        base_path = (
            pathlib.Path(app.config["DATA_PATH"]) / defaults.RESOURCE_DATA
        ).resolve()

        # security check for argument from url
        full_attachment_path = base_path / attachment_path
        try:
            full_attachment_path.relative_to(base_path)
        except ValueError:
            raise werkzeug.exceptions.NotAcceptable()

        if not full_attachment_path.is_file():
            raise werkzeug.exceptions.NotFound()

        return send_from_directory(
            directory=full_attachment_path.parent,
            path=full_attachment_path.name,
        )


@_api.route("/api/v1/metadata/fix-spec/tags")
class FixTags(Resource):
    def get(self):
        """Get meta data which is used to parse Testplan report."""
        return jsonify(FIX_SPEC["tags"])


@_api.route("/api/v1/metadata/fix-spec/tags/<int:num>/enum-vals")
class FixTagValueChoices(Resource):
    def get(self, num):
        """Get meta data which is used to parse Testplan report."""
        return jsonify(FIX_SPEC["enum_vals_by_tag"].get(num, []))


class WebServer(Thread):
    def __init__(
        self,
        port=defaults.WEB_SERVER_PORT,
        static_path=TESTPLAN_UI_STATIC_DIR,
        data_path="./",
        report_name=TESTPLAN_REPORT,
    ):
        super(WebServer, self).__init__()
        self.host = defaults.WEB_SERVER_HOSTNAME
        self.port = port
        self.static_path = static_path
        self.data_path = data_path
        self.report_name = report_name
        self.server = None

    def _configure_flask_app(self):
        app.config["STATIC_PATH"] = self.static_path
        app.config["DATA_PATH"] = self.data_path
        app.config["TESTPLAN_REPORT_NAME"] = self.report_name
        app.static_folder = os.path.abspath(
            os.path.join(
                app.config["STATIC_PATH"], "testing", "build", "static"
            )
        )

    def run(self):
        self._configure_flask_app()
        dispatcher = PathInfoDispatcher({"/": app})
        self.server = WSGIServer((self.host, self.port), dispatcher)
        self.server.start()

    def ready(self):
        if self.server:
            return self.server.ready
        return False

    def stop(self):
        self.server.stop()
        self.server = None


if __name__ == "__main__":
    args = parse_cli_args()

    if args.static_path:
        app.config["STATIC_PATH"] = args.static_path
    else:
        app.config["STATIC_PATH"] = pwd()
    app.static_folder = os.path.abspath(
        os.path.join(app.config["STATIC_PATH"], "testing", "build", "static")
    )
    if args.data_path:
        app.config["DATA_PATH"] = args.data_path
    else:
        # In future if not looking up data from the local file system
        # we will be looking it up from a database.
        app.config["DATA_PATH"] = pwd()
    if args.report_name:
        app.config["TESTPLAN_REPORT_NAME"] = args.report_name
    else:
        app.config["TESTPLAN_REPORT_NAME"] = "report.json"

    print("Running Testplan web app on 0.0.0.0...")
    app.run(host="0.0.0.0", port=0)
