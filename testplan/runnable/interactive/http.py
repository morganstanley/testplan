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
import uuid
from multiprocessing import dummy

import flask
import flask_restplus
from cheroot import wsgi
import werkzeug.exceptions
import marshmallow.exceptions

from testplan.common.config import ConfigOption
from testplan.common.entity import Entity, EntityConfig, RunnableIHandler
from testplan import defaults
from testplan import report


def generate_interactive_api(http_handler, ihandler):
    """Generates the interactive API using Flask."""
    app = flask.Flask(__name__)
    api = flask_restplus.Api(app)

    @api.route("/api/v1/interactive/report")
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

                if should_run(ihandler.report.status):
                    new_report.status = report.Status.RUNNING
                    http_handler.pool.apply_async(ihandler.run_tests)

                ihandler.report = new_report
                return ihandler.report.shallow_serialize()

    @api.route("/api/v1/interactive/report/tests")
    class Tests(flask_restplus.Resource):
        """
        Tests endpoint. Represents all Test objects in the report. Read-only.
        """

        def get(self):
            """Get the UIDs of all tests defined in the testplan."""
            with ihandler.report_mutex:
                return [test.uid for test in ihandler.report]

    @api.route("/api/v1/interactive/report/tests/<string:test_uid>")
    class Test(flask_restplus.Resource):
        """
        Test endpoint. Represents a single Test object in the testplan with
        corresponding UID.
        """

        def get(self, test_uid):
            """Get the state of a specific test from the testplan."""
            with ihandler.report_mutex:
                try:
                    return ihandler.report[test_uid].shallow_serialize()
                except KeyError:
                    raise werkzeug.exceptions.NotFound

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

                if should_run(current_test.status):
                    new_test.status = report.Status.RUNNING
                    http_handler.pool.apply_async(
                        ihandler.run_test, (test_uid,)
                    )

                ihandler.report[test_uid] = new_test
                return ihandler.report[test_uid].shallow_serialize()

    @api.route("/api/v1/interactive/report/tests/<string:test_uid>/suites")
    class Suites(flask_restplus.Resource):
        """
        Suites endpoint. Represents all test suites within a Test object.
        """

        def get(self, test_uid):
            """Get the UIDs of all test suites owned by a specific test."""
            try:
                return [entry.uid for entry in ihandler.report[test_uid]]
            except KeyError:
                raise werkzeug.exceptions.NotFound

    @api.route(
        "/api/v1/interactive/report/tests/<string:test_uid>/suites/"
        "<string:suite_uid>"
    )
    class Suite(flask_restplus.Resource):
        """
        Suite endpoint. Represents a single test suite within a Test object
        with the mathcing test and suite UIDs.
        """

        def get(self, test_uid, suite_uid):
            """Get the state of a specific test suite."""
            with ihandler.report_mutex:
                try:
                    return ihandler.report[test_uid][
                        suite_uid
                    ].shallow_serialize()
                except KeyError:
                    raise werkzeug.exceptions.NotFound

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

                if should_run(current_suite.status):
                    new_suite.status = report.Status.RUNNING
                    http_handler.pool.apply_async(
                        ihandler.run_test_suite, (test_uid, suite_uid)
                    )

                ihandler.report[test_uid][suite_uid] = new_suite
                return ihandler.report[test_uid][suite_uid].shallow_serialize()

    @api.route(
        "/api/v1/interactive/report/tests/<string:test_uid>/suites/"
        "<string:suite_uid>/testcases"
    )
    class Testcases(flask_restplus.Resource):
        """
        Testcases endpoint. Represents all testcases within a test suite
        within a Test object, with the matching test and suite UIDs.
        """

        def get(self, test_uid, suite_uid):
            """Get the UIDs of all testcases defined on a suite."""
            with ihandler.report_mutex:
                try:
                    return [
                        entry.uid
                        for entry in ihandler.report[test_uid][suite_uid]
                    ]
                except KeyError:
                    raise werkzeug.exceptions.NotFound

    @api.route(
        "/api/v1/interactive/report/tests/<string:test_uid>/suites/"
        "<string:suite_uid>/testcases/<string:testcase_uid>"
    )
    class Testcase(flask_restplus.Resource):
        """
        Testcases endpoint. Represents a single testcase within a test
        suite, within a Test object, with the matching test, suite and
        testcase UIDs.
        """

        def get(self, test_uid, suite_uid, testcase_uid):
            """Get the state of a specific testcase."""
            with ihandler.report_mutex:
                try:
                    return ihandler.report[test_uid][suite_uid][
                        testcase_uid
                    ].serialize()
                except KeyError:
                    raise werkzeug.exceptions.NotFound

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
                    new_testcase = report.TestCaseReport.deserialize(
                        flask.request.json
                    )
                except marshmallow.exceptions.ValidationError as e:
                    raise werkzeug.exceptions.BadRequest(str(e))

                if should_run(current_testcase.status):
                    new_testcase.status = report.Status.RUNNING
                    http_handler.pool.apply_async(
                        ihandler.run_test_case,
                        (test_uid, suite_uid, testcase_uid),
                    )

                suite[testcase_uid] = new_testcase
                return suite[testcase_uid].serialize()

    def should_run(curr_status):
        """
        Check if any test(s) should be triggered to run from a state
        update.

        The only allowed state transition on update is ready -> running.
        Otherwise the state must be unchanged. If the new status is invalid
        a BadRequest exception will be raised.
        """
        try:
            new_status = flask.request.json["status"]
        except KeyError:
            raise werkzeug.exceptions.BadRequest("status is required")

        if new_status == curr_status:
            return False
        elif new_status == "running":
            return True
        else:
            raise werkzeug.exceptions.BadRequest(
                "Cannot update status to {}".format(new_status)
            )

    return app, api


class TestRunnerHTTPHandlerConfig(EntityConfig):
    """
    Configuration object for
    :py:class:`~testplan.runnable.interactive.http.TestRunnerHTTPHandler`
    entity.
    """

    @classmethod
    def get_options(cls):
        return {
            "ihandler": RunnableIHandler,
            ConfigOption("host", default=defaults.WEB_SERVER_HOSTNAME): str,
            ConfigOption("port", default=defaults.WEB_SERVER_HOSTNAME): int,
            ConfigOption("pool_size", default=4): int,
        }


class TestRunnerHTTPHandler(Entity):
    """
    Server that invokes an interactive handler to perform dynamic operations.

    :param ihandler: Runnable interactive handler instance.
    :type ihandler: Subclass of :py:class:
        `RunnableIHandler <testplan.common.entity.base.RunnableIHandler>`
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
        self.task_pool = None
        self.tasks = {}

    @property
    def host(self):
        if self._server is None or not self._server.ready:
            return None
        return self._server.bind_addr[0]

    @property
    def port(self):
        if self._server is None or not self._server.ready:
            return None
        return self._server.bind_addr[1]

    def run(self):
        """
        Runs the threader HTTP handler for interactive mode.
        """
        app, _ = generate_interactive_api(self, self.cfg.ihandler)
        self._server = wsgi.Server((self.cfg.host, self.cfg.port), app)

        # Cannot use context manager on Python 2 to use try/finally to ensure
        # pool resources are cleaned up.
        self.pool = dummy.Pool(self.cfg.pool_size)
        try:
            self._server.start()
        finally:
            self.pool.terminate()
            self.pool.join()

