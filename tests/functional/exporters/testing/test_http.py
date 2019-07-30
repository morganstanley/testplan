import os
import json
import threading
import tempfile

from six.moves.BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import Testplan
from testplan.common.utils.testing import (
    log_propagation_disabled, argv_overridden
)
from testplan.exporters.testing import HTTPExporter
from testplan.common.utils.logger import TESTPLAN_LOGGER

data_file = tempfile.mkstemp()[1]


class PostHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        # Handle request, load JSON data and save it to file
        assert 'application/json' in self.headers['Content-Type'].lower()
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(self.data_string)

        with open(data_file, 'w') as fp:
            json.dump(data, fp)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()


@testsuite
class Alpha(object):

    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, 'equality description')

    @testcase
    def test_membership(self, env, result):
        result.contain(1, [1, 2, 3])


@testsuite
class Beta(object):

    @testcase
    def test_failure(self, env, result):
        result.equal(1, 2, 'failing assertion')
        result.equal(5, 10)

    @testcase
    def test_error(self, env, result):
        raise Exception('foo')


def test_http_exporter(tmpdir):
    """
    HTTP Exporter should send a json report to the given `http_url`.
    """
    server = HTTPServer(("", 0), PostHandler)
    http_url = 'http://localhost:{}'.format(server.server_port)
    start_thread = threading.Thread(target=server.serve_forever)
    start_thread.daemon = True
    start_thread.start()

    if os.path.exists(data_file):
        os.remove(data_file)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        plan = Testplan(
            name='plan', parse_cmdline=False,
            exporters=HTTPExporter(url=http_url)
        )
        multitest_1 = MultiTest(name='Primary', suites=[Alpha()])
        multitest_2 = MultiTest(name='Secondary', suites=[Beta()])
        plan.add(multitest_1)
        plan.add(multitest_2)
        plan.run()

    assert os.path.exists(data_file)
    assert os.stat(data_file).st_size > 0
    os.remove(data_file)

    shutdown_thread = threading.Thread(target=server.serve_forever)
    shutdown_thread.daemon = True
    shutdown_thread.start()


def test_implicit_exporter_initialization(tmpdir):
    """
    An implicit exporting should be done if `http_url` is available
    via cmdline args but no exporters were declared programmatically.
    """
    server = HTTPServer(("", 0), PostHandler)
    http_url = 'http://localhost:{}'.format(server.server_port)
    start_thread = threading.Thread(target=server.serve_forever)
    start_thread.daemon = True
    start_thread.start()

    if os.path.exists(data_file):
        os.remove(data_file)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        with argv_overridden('--http', http_url):
            plan = Testplan(name='plan')
            multitest_1 = MultiTest(name='Primary', suites=[Alpha()])
            plan.add(multitest_1)
            plan.run()

    assert os.path.exists(data_file)
    assert os.stat(data_file).st_size > 0
    os.remove(data_file)

    shutdown_thread = threading.Thread(target=server.serve_forever)
    shutdown_thread.daemon = True
    shutdown_thread.start()
