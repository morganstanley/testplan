"""Test the JSON exporter."""
import json
import os
import tempfile

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import Testplan
from testplan.common.utils.testing import (
    log_propagation_disabled, argv_overridden
)
from testplan.exporters.testing import JSONExporter
from testplan.common.utils.logger import TESTPLAN_LOGGER


@testsuite
class Alpha(object):

    @testcase
    def test_comparison(self, env, result):
        result.equal(1, 1, 'equality description')

    @testcase
    def test_membership(self, env, result):
        result.contain(1, [1, 2, 3])

    @testcase
    def test_attach(self, env, result):
        """Test attaching a file to the report."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmpfile:
            tmpfile.write("testplan\n" * 100)

        result.attach(tmpfile.name)


@testsuite
class Beta(object):

    @testcase
    def test_failure(self, env, result):
        result.equal(1, 2, 'failing assertion')
        result.equal(5, 10)

    @testcase
    def test_error(self, env, result):
        raise Exception('foo')


def test_json_exporter(tmpdir):
    """
    JSON Exporter should generate a json report at the given `json_path`.
    """
    json_path = tmpdir.mkdir('reports').join('report.json').strpath

    with log_propagation_disabled(TESTPLAN_LOGGER):
        plan = Testplan(
            name='plan', parse_cmdline=False,
            exporters=JSONExporter(json_path=json_path)
        )
        multitest_1 = MultiTest(name='Primary', suites=[Alpha()])
        multitest_2 = MultiTest(name='Secondary', suites=[Beta()])
        plan.add(multitest_1)
        plan.add(multitest_2)
        plan.run()

    assert os.path.exists(json_path)
    assert os.stat(json_path).st_size > 0

    # Load the JSON file to validate it contains valid JSON.
    with open(json_path) as json_file:
        report = json.load(json_file)

    # Check that the expected text file is attached correctly.
    attachments_dir = os.path.join(os.path.dirname(json_path), "_attachments")
    assert os.path.isdir(attachments_dir)
    assert len(report["attachments"]) == 1
    dst_path = list(report["attachments"].keys())[0]
    attachment_filepath = os.path.join(attachments_dir, dst_path)
    assert os.path.isfile(attachment_filepath)
    with open(attachment_filepath) as f:
        attachment_file_contents = f.read()
    assert attachment_file_contents == "testplan\n" * 100


def test_implicit_exporter_initialization(tmpdir):
    """
    An implicit JSON should be generated if `json_path` is available
    via cmdline args but no exporters were declared programmatically.
    """
    json_path = tmpdir.mkdir('reports').join('report.json').strpath

    with log_propagation_disabled(TESTPLAN_LOGGER):
        with argv_overridden('--json', json_path):
            plan = Testplan(name='plan')
            multitest_1 = MultiTest(name='Primary', suites=[Alpha()])
            plan.add(multitest_1)
            plan.run()

    assert os.path.exists(json_path)
    assert os.stat(json_path).st_size > 0

    # Load the JSON file to validate it contains valid JSON.
    with open(json_path) as json_file:
        json.load(json_file)
