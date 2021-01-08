"""
Http handler for interactive mode.
"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import super
from builtins import str
from future import standard_library

standard_library.install_aliases()
import os
import time
import functools
import traceback

import flask
import flask_restplus
import flask_restplus.fields
from flask import request
from cheroot import wsgi
import werkzeug.exceptions
import marshmallow.exceptions
from six.moves.urllib.parse import unquote_plus

import testplan
from testplan.common.config import ConfigOption
from testplan.common.utils import strings
from testplan.common import entity
from testplan import defaults
from testplan import report
from .reloader import ModuleReloader


def decode_uri_component(func):
    """Decode URI component before arguments passed to url route handler."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        new_kwargs = {key: unquote_plus(val) for key, val in kwargs.items()}
        return func(*args, **new_kwargs)

    return wrapper


def generate_interactive_api(ihandler):
    """Generates the interactive API using Flask."""
    build_directory = os.path.join(
        os.path.dirname(testplan.__file__), "web_ui", "testing", "build"
    )
    static_dir = os.path.join(build_directory, "static")

    api_prefix = "/api/v1/interactive"
    api_blueprint = flask.Blueprint("api", "testplan")
    api = flask_restplus.Api(api_blueprint)
    app = flask.Flask("testplan", static_folder=static_dir)
    app.register_blueprint(api_blueprint, url_prefix=api_prefix)

    post_export_model = api.model(
        "Save report",
        {
            "exporters": flask_restplus.fields.List(
                flask_restplus.fields.String(example="PDFExporter")
            )
        },
    )

    export_history = []

    @app.route("/interactive/")
    @app.route("/interactive/<path:subpath>")
    def interactive(subpath=None):
        """
        Main entry point for the interactive mode UI page. Serves the static
        index.html from the UI app's build directory. We serve the app at
        /interactive and not just at /index.html or at / because the same app
        is used for batch and interactive report, and the way it
        distinguishes between the two modes is by the URL.
        """
        return flask.send_from_directory(build_directory, "index.html")

    @app.route("/<path:filename>")
    def serve_static(filename):
        """
        Serve all static files (HTML, JS, CSS, images etc.) at the root path.
        """
        return flask.send_from_directory(build_directory, filename)

    @app.after_request
    def add_cache_control_headers(response):
        """
        Disable browser caching for all HTTP requests, so that the most
        up-to-date data is always returned.
        """
        response.headers["Cache-Control"] = "no-cache"
        return response

    @api.route("/report")
    class Report(flask_restplus.Resource):
        """
        Interactive report endpoint. There is a single root report object
        for interactive mode.
        """

        def get(self):
            """Get the state of the root interactive report."""
            with ihandler.report_mutex:
                return ihandler.report.shallow_serialize()

        def put(self):
            """Update the state of the root interactive report."""
            if flask.request.json is None:
                raise werkzeug.exceptions.BadRequest(
                    "JSON body is required for PUT"
                )

            with ihandler.report_mutex:
                try:
                    new_report = report.TestReport.shallow_deserialize(
                        flask.request.json, ihandler.report
                    )
                except marshmallow.exceptions.ValidationError as e:
                    raise werkzeug.exceptions.BadRequest(str(e))

                _check_uids_match(ihandler.report.uid, new_report.uid)

                if _should_run(ihandler.report.runtime_status):
                    new_report.runtime_status = report.RuntimeStatus.RUNNING
                    ihandler.run_all_tests(await_results=False)

                ihandler.report = new_report
                return ihandler.report.shallow_serialize()

    @api.route("/report/tests")
    class AllTests(flask_restplus.Resource):
        """
        Tests endpoint. Represents all Test objects in the report. Read-only.
        """

        def get(self):
            """Get the UIDs of all tests defined in the testplan."""
            with ihandler.report_mutex:
                return [test.shallow_serialize() for test in ihandler.report]

    @api.route("/report/tests/<string:test_uid>")
    class SingleTest(flask_restplus.Resource):
        """
        Test endpoint. Represents a single Test object in the testplan with
        corresponding UID.
        """

        _ENV_TRANSITIONS = {
            entity.ResourceStatus.STOPPED: (
                entity.ResourceStatus.STARTING,
                ihandler.start_test_resources,
            ),
            entity.ResourceStatus.STARTED: (
                entity.ResourceStatus.STOPPING,
                ihandler.stop_test_resources,
            ),
        }

        @decode_uri_component
        def get(self, test_uid):
            """Get the state of a specific test from the testplan."""
            with ihandler.report_mutex:
                try:
                    return ihandler.report[test_uid].shallow_serialize()
                except KeyError:
                    raise werkzeug.exceptions.NotFound

        @decode_uri_component
        def put(self, test_uid):
            """Update the state of a specific test."""
            if flask.request.json is None:
                raise werkzeug.exceptions.BadRequest(
                    "JSON body is required for PUT"
                )

            with ihandler.report_mutex:
                try:
                    current_test = ihandler.report[test_uid]
                except KeyError:
                    raise werkzeug.exceptions.NotFound

                try:
                    new_test = report.TestGroupReport.shallow_deserialize(
                        flask.request.json, current_test
                    )
                except marshmallow.exceptions.ValidationError as e:
                    raise werkzeug.exceptions.BadRequest(str(e))

                _check_uids_match(current_test.uid, new_test.uid)

                # Trigger a side-effect if either the report or environment
                # statuses have been updated.
                if _should_run(current_test.runtime_status):
                    if current_test.env_status != new_test.env_status:
                        raise werkzeug.exceptions.BadRequest(
                            "env_status cannot change when test status is "
                            "changing. Current env status is {}".format(
                                current_test.env_status
                            )
                        )

                    new_test.runtime_status = report.RuntimeStatus.RUNNING
                    ihandler.run_test(test_uid, await_results=False)
                else:
                    env_action = self._check_env_transition(
                        current_test.env_status, new_test.env_status
                    )
                    if env_action is not None:
                        env_action(test_uid, await_results=False)

                ihandler.report[test_uid] = new_test
                return ihandler.report[test_uid].shallow_serialize()

        def _check_env_transition(self, current_state, new_state):
            """
            Validate the new environment state by comparing with the current
            state. Only updates which leave the environment status unchanged
            or which follow an allowed transition will be accepted.

            Returns an action if one is required, or else None.
            """
            if current_state == new_state:
                return None

            allowed_transition, action = self._ENV_TRANSITIONS.get(
                current_state, (None, None)
            )
            if allowed_transition is None or new_state != allowed_transition:
                raise werkzeug.exceptions.BadRequest(
                    "Cannot transition environment state from {} to {}".format(
                        current_state, new_state
                    )
                )

            return action

    @api.route("/report/tests/<string:test_uid>/suites")
    class AllSuites(flask_restplus.Resource):
        """
        Suites endpoint. Represents all test suites within a Test object.
        """

        @decode_uri_component
        def get(self, test_uid):
            """Get the UIDs of all test suites owned by a specific test."""
            try:
                return [
                    entry.shallow_serialize()
                    for entry in ihandler.report[test_uid]
                ]
            except KeyError:
                raise werkzeug.exceptions.NotFound

    @api.route("/report/tests/<string:test_uid>/suites/<string:suite_uid>")
    class SingleSuite(flask_restplus.Resource):
        """
        Suite endpoint. Represents a single test suite within a Test object
        with the matching test and suite UIDs.
        """

        @decode_uri_component
        def get(self, test_uid, suite_uid):
            """Get the state of a specific test suite."""
            with ihandler.report_mutex:
                try:
                    return ihandler.report[test_uid][
                        suite_uid
                    ].shallow_serialize()
                except KeyError:
                    raise werkzeug.exceptions.NotFound

        @decode_uri_component
        def put(self, test_uid, suite_uid):
            """Update the state of a specific test suite."""
            if flask.request.json is None:
                raise werkzeug.exceptions.BadRequest(
                    "JSON body is required for PUT"
                )

            with ihandler.report_mutex:
                try:
                    current_suite = ihandler.report[test_uid][suite_uid]
                except KeyError:
                    raise werkzeug.exceptions.NotFound

                try:
                    new_suite = report.TestGroupReport.shallow_deserialize(
                        flask.request.json, current_suite
                    )
                except marshmallow.exceptions.ValidationError as e:
                    raise werkzeug.exceptions.BadRequest(str(e))

                _check_uids_match(current_suite.uid, new_suite.uid)

                if _should_run(current_suite.runtime_status):
                    new_suite.runtime_status = report.RuntimeStatus.RUNNING
                    ihandler.run_test_suite(
                        test_uid, suite_uid, await_results=False
                    )

                ihandler.report[test_uid][suite_uid] = new_suite
                return ihandler.report[test_uid][suite_uid].shallow_serialize()

    @api.route(
        "/report/tests/<string:test_uid>/suites/<string:suite_uid>/testcases"
    )
    class AllTestcases(flask_restplus.Resource):
        """
        Testcases endpoint. Represents all testcases within a test suite
        within a Test object, with the matching test and suite UIDs.
        """

        @decode_uri_component
        def get(self, test_uid, suite_uid):
            """Get the UIDs of all testcases defined on a suite."""
            with ihandler.report_mutex:
                try:
                    return [
                        _serialize_testcase(entry)
                        for entry in ihandler.report[test_uid][suite_uid]
                    ]
                except KeyError:
                    raise werkzeug.exceptions.NotFound

    @api.route(
        "/report/tests/<string:test_uid>/suites/<string:suite_uid>/testcases"
        "/<string:testcase_uid>"
    )
    class SingleTestcase(flask_restplus.Resource):
        """
        Testcases endpoint. Represents a single testcase within a test
        suite, within a Test object, with the matching test, suite and
        testcase UIDs.
        """

        @decode_uri_component
        def get(self, test_uid, suite_uid, testcase_uid):
            """Get the state of a specific testcase."""
            with ihandler.report_mutex:
                try:
                    report_entry = ihandler.report[test_uid][suite_uid][
                        testcase_uid
                    ]
                except KeyError:
                    raise werkzeug.exceptions.NotFound

                return _serialize_testcase(report_entry)

        @decode_uri_component
        def put(self, test_uid, suite_uid, testcase_uid):
            """Update the state of a specific testcase."""
            if flask.request.json is None:
                raise werkzeug.exceptions.BadRequest(
                    "JSON body is required for PUT"
                )

            with ihandler.report_mutex:
                suite = ihandler.report[test_uid][suite_uid]
                try:
                    current_testcase = suite[testcase_uid]
                except KeyError:
                    raise werkzeug.exceptions.NotFound

                try:
                    new_testcase = _deserialize_testcase(
                        current_testcase, flask.request.json
                    )
                except marshmallow.exceptions.ValidationError as e:
                    raise werkzeug.exceptions.BadRequest(str(e))

                _check_uids_match(current_testcase.uid, new_testcase.uid)

                if _should_run(current_testcase.runtime_status):
                    new_testcase.runtime_status = report.RuntimeStatus.RUNNING
                    ihandler.run_test_case(
                        test_uid, suite_uid, testcase_uid, await_results=False
                    )

                suite[testcase_uid] = new_testcase
                return _serialize_testcase(suite[testcase_uid])

    @api.route(
        "/report/tests/<string:test_uid>/suites/<string:suite_uid>/testcases"
        "/<string:testcase_uid>/parametrizations"
    )
    class AllParametrizations(flask_restplus.Resource):
        """
        Parametrizations endpoint. Represents all parametrizations of a single
        testcase.
        """

        @decode_uri_component
        def get(self, test_uid, suite_uid, testcase_uid):
            """Get the state of all parametrizations of a testcase."""
            with ihandler.report_mutex:
                try:
                    return [
                        entry.serialize()
                        for entry in ihandler.report[test_uid][suite_uid][
                            testcase_uid
                        ]
                    ]
                except KeyError:
                    raise werkzeug.exceptions.NotFound

    @api.route(
        "/report/tests/<string:test_uid>/suites/<string:suite_uid>/testcases"
        "/<string:testcase_uid>/parametrizations/<string:param_uid>"
    )
    class ParamatrizedTestCase(flask_restplus.Resource):
        """
        Paramatrized testcase endpoint. Represents a single testcase within
        a paramatrization group, with a unique combination of parameters.
        """

        @decode_uri_component
        def get(self, test_uid, suite_uid, testcase_uid, param_uid):
            """Get the state of a specific paramatrized testcase."""
            with ihandler.report_mutex:
                try:
                    report_entry = ihandler.report[test_uid][suite_uid][
                        testcase_uid
                    ][param_uid]
                except KeyError:
                    raise werkzeug.exceptions.NotFound

                return report_entry.serialize()

        @decode_uri_component
        def put(self, test_uid, suite_uid, testcase_uid, param_uid):
            """Update the state of a specific parametrized testcase."""
            if flask.request.json is None:
                raise werkzeug.exceptions.BadRequest(
                    "JSON body is required for PUT"
                )

            with ihandler.report_mutex:
                try:
                    param_group = ihandler.report[test_uid][suite_uid][
                        testcase_uid
                    ]
                    current_testcase = param_group[param_uid]
                except KeyError:
                    raise werkzeug.exceptions.NotFound

                try:
                    new_testcase = report.TestCaseReport.deserialize(
                        flask.request.json
                    )
                except marshmallow.exceptions.ValidationError as e:
                    raise werkzeug.exceptions.BadRequest(str(e))

                _check_uids_match(current_testcase.uid, new_testcase.uid)

                if _should_run(current_testcase.runtime_status):
                    new_testcase.runtime_status = report.RuntimeStatus.RUNNING
                    ihandler.run_test_case_param(
                        test_uid,
                        suite_uid,
                        testcase_uid,
                        param_uid,
                        await_results=False,
                    )

                param_group[param_uid] = new_testcase
                return param_group[param_uid].serialize()

    @api.route("/report/export")
    class ExportReport(flask_restplus.Resource):
        """
        Interactive export endpoint. There is an API for exporting root
        report object.
        """

        def get(self):
            available_exporters = []
            with ihandler.report_mutex:
                for exporter in ihandler.exporters:
                    available_exporters.append(exporter.name)
            return {
                "available": available_exporters,
                "history": export_history,
            }

        @api.expect(post_export_model)
        def post(self):
            save_exports = request.json
            with ihandler.report_mutex:
                for exporter in ihandler.exporters:
                    if exporter.name in save_exports.get("exporters", []):
                        export_result = {
                            "time": time.time(),
                            "name": exporter.name,
                            "uid": strings.uuid4(),
                        }
                        try:
                            export_path = exporter.export(ihandler.report)
                            export_result["success"] = True
                            export_result["message"] = export_path
                        except Exception:
                            export_result["success"] = False
                            export_result["message"] = traceback.format_exc()
                        export_history.append(export_result)
            return {"history": export_history}

    @api.route("/report/export/<string:uid>")
    class ExporterFile(flask_restplus.Resource):
        """
        Interactive export download endpoint. There is an API for downloading
        report file.
        """

        def get(self, uid):
            for export in export_history:
                if export["uid"] == uid:
                    return flask.send_file(export["message"])
            raise werkzeug.exceptions.NotFound

    @api.route("/attachments")
    class AllAttachments(flask_restplus.Resource):
        """
        Represents all files currently attached to the Testplan interactive
        report.
        """

        def get(self):
            """Return a list of all attachment UIDs."""
            with ihandler.report_mutex:
                return list(ihandler.report.attachments.keys())

    @api.route("/attachments/<path:attachment_uid>")
    class SingleAttachment(flask_restplus.Resource):
        """
        Represents a specific file attached to the Testplan interactive report.
        """

        def get(self, attachment_uid):
            """Get a file attachment."""
            with ihandler.report_mutex:
                try:
                    filepath = ihandler.report.attachments[attachment_uid]
                except KeyError:
                    raise werkzeug.exceptions.NotFound

            return flask.send_file(filepath)

    @api.route("/reload")
    class ReloadCode(flask_restplus.Resource):
        """
        Reload source code.
        """

        def get(self):
            try:
                ihandler.reload(rebuild_dependencies=True)
                ihandler.reload_report()
            except Exception as ex:
                ihandler.logger.error("Reload failed! %s ", str(ex))
            return True

    return app, api


def _serialize_testcase(report_entry):
    """
    Serialize a report entry representing a testcase. Since the
    testcase may be parametrized, we check for that and return
    the shallow serialization instead.
    """
    if isinstance(report_entry, report.TestCaseReport):
        return report_entry.serialize()
    elif isinstance(report_entry, report.TestGroupReport):
        return report_entry.shallow_serialize()
    else:
        raise TypeError(
            "Unexpected report entry type: {}".format(type(report_entry))
        )


def _deserialize_testcase(current_testcase, serialized):
    """
    Deserialize an updated testcase entry.

    We need to inspect the type of the current testcase
    object in order to decide how to deserialize the update.
    If a testcase is parametrized, it will be represented
    as a TestGroupReport type at this level of the report
    tree. Non-parametrized testcases are represented
    as a TestCaseReport.
    """
    if isinstance(current_testcase, report.TestCaseReport):
        return report.TestCaseReport.deserialize(serialized)
    elif isinstance(current_testcase, report.TestGroupReport):
        return report.TestGroupReport.shallow_deserialize(
            serialized, current_testcase
        )
    else:
        raise TypeError("Unexpected report type %s", type(current_testcase))


def _should_run(curr_status):
    """
    Check if any test(s) should be triggered to run from a state
    update.

    The only allowed state transition on update is to set the status
    to RUNNING to trigger test(s) to run. Any other state update (e.g.
    setting the state of a running test to PASSED) is not allowed - only
    the server may make those transitions. A BadRequest exception will be
    raised if the requested status is not valid.

    TODO: from api design perspective, _should_run should take a curr_status
    and a new_status, rather than looking at request directly
    """
    try:
        new_status = flask.request.json["runtime_status"]
    except KeyError:
        raise werkzeug.exceptions.BadRequest("runtime_status is required")

    if new_status == curr_status:
        return False
    elif new_status == report.RuntimeStatus.RUNNING:
        return True
    else:
        raise werkzeug.exceptions.BadRequest(
            "Cannot update runtime status from {} to {}".format(
                curr_status, new_status
            )
        )


def _check_uids_match(current_uid, new_uid):
    """
    Check that the UID from the updated entry matches the current one.
    UIDs cannot be changed, so raise a BadRequest error if they do not
    match.
    """
    if new_uid != current_uid:
        raise werkzeug.exceptions.BadRequest(
            "Cannot update UID of entry from {} to {}".format(
                current_uid, new_uid
            )
        )


class TestRunnerHTTPHandlerConfig(entity.EntityConfig):
    """
    Configuration object for
    :py:class:`~testplan.runnable.interactive.http.TestRunnerHTTPHandler`
    entity.
    """

    @classmethod
    def get_options(cls):
        return {
            "ihandler": entity.Entity,
            ConfigOption("host", default=defaults.WEB_SERVER_HOSTNAME): str,
            ConfigOption("port", default=defaults.WEB_SERVER_PORT): int,
            ConfigOption(
                "pool_size", default=defaults.INTERACTIVE_POOL_SIZE
            ): int,
        }


class TestRunnerHTTPHandler(entity.Entity):
    """
    Server that invokes an interactive handler to perform dynamic operations.

    :param ihandler: Runnable interactive handler instance.
    :type ihandler: ``Entity``
    :param host: Host to bind to.
    :type host: ``str``
    :param port: Port to bind to.
    :type port: ``int``

    Also inherits all
    :py:class:`~testplan.common.entity.base.Entity` options.
    """

    CONFIG = TestRunnerHTTPHandlerConfig

    def __init__(self, **options):
        super(TestRunnerHTTPHandler, self).__init__(**options)
        self._server = None

    @property
    def bind_addr(self):
        """
        :return: Bound host and port of HTTP server, or None if not bound.
        :rtype: ``Optional[Tuple[str, int]]``
        """
        if self._server is None:
            return None
        else:
            return self._server.bind_addr

    def setup(self):
        """
        Generate the flask App and prepare the HTTP server.

        :return: server host and port tuple
        :rtype: ``Tuple[str, int]``
        """
        app, _ = generate_interactive_api(self.cfg.ihandler)
        self._server = wsgi.Server((self.cfg.host, self.cfg.port), app)
        self._server.prepare()

        return self._server.bind_addr

    def run(self):
        """
        Start serving requests. Will block until the server stops running.
        """
        if self._server is None:
            raise RuntimeError("Run setup() before run()")
        try:
            self._server.serve()
        finally:
            self._server = None
