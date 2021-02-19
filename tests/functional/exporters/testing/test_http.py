import json
import threading

import pytest
from six.moves.BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from testplan.testing import multitest
from testplan import TestplanMock
from testplan.common.utils.testing import argv_overridden
from testplan.exporters.testing import HTTPExporter


class PostHandler(BaseHTTPRequestHandler):
    """Handles POST requests by extracting JSON data and storing in a queue."""

    post_data = []

    def do_POST(self):
        """Handle request, load JSON data and store it in a queue."""
        assert "application/json" in self.headers["Content-Type"].lower()
        content_length = int(self.headers["Content-Length"])

        # self.rfile is opened in binary mode so we need to .decode() the
        # contents into a unicode string.
        data_string = self.rfile.read(content_length).decode()
        self.post_data.append(json.loads(data_string))

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()


@multitest.testsuite
class Alpha(object):
    @multitest.testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, "equality description")

    @multitest.testcase
    def test_membership(self, env, result):
        result.contain(1, [1, 2, 3])


@multitest.testsuite
class Beta(object):
    @multitest.testcase
    def test_failure(self, env, result):
        result.equal(1, 2, "failing assertion")
        result.equal(5, 10)

    @multitest.testcase
    def test_error(self, env, result):
        raise Exception("foo")


@pytest.fixture(scope="module")
def http_server():
    """
    Yields an HTTP server object, which stores JSON data from received POST
    requests in a .post_data queue.
    """
    PostHandler.post_data = []
    server = HTTPServer(("", 0), PostHandler)
    start_thread = threading.Thread(target=server.serve_forever)
    start_thread.daemon = True
    start_thread.start()

    yield server

    server.shutdown()
    start_thread.join()


def test_http_exporter(runpath, http_server):
    """
    HTTP Exporter should send a json report to the given `http_url`.
    """
    http_url = "http://localhost:{}".format(http_server.server_port)

    plan = TestplanMock(
        "plan", exporters=HTTPExporter(http_url=http_url), runpath=runpath
    )
    multitest_1 = multitest.MultiTest(name="Primary", suites=[Alpha()])
    multitest_2 = multitest.MultiTest(name="Secondary", suites=[Beta()])
    plan.add(multitest_1)
    plan.add(multitest_2)
    plan.run()

    assert len(PostHandler.post_data) == 1
    PostHandler.post_data.pop()


def test_implicit_exporter_initialization(runpath, http_server):
    """
    An implicit exporting should be done if `http_url` is available
    via cmdline args but no exporters were declared programmatically.
    """
    http_url = "http://localhost:{}".format(http_server.server_port)

    with argv_overridden("--http", http_url):
        plan = TestplanMock("plan", parse_cmdline=True, runpath=runpath)
        multitest_1 = multitest.MultiTest(name="Primary", suites=[Alpha()])
        plan.add(multitest_1)
        plan.run()

    assert len(PostHandler.post_data) == 1
    PostHandler.post_data.pop()
