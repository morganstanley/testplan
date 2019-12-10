"""Functional tests for interactive HTTP API."""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()
import functools

import six
import pytest
import requests

import testplan
from testplan import report
from testplan.testing import multitest
from testplan.common.utils import timing

from tests.unit.testplan.runnable.interactive import test_api


@multitest.testsuite
class ExampleSuite(object):
    """Example test suite."""

    @multitest.testcase
    def test_passes(self, env, result):
        """Testcase that passes."""
        result.true(True)

    @multitest.testcase
    def test_fails(self, env, result):
        """Testcase that fails."""
        result.true(False)

    @multitest.testcase
    def test_logs(self, env, result):
        """Testcase that makes a log."""
        result.log("Here I share my deepest thoughts")


@pytest.fixture
def plan():
    """Yield an interactive testplan."""
    plan = testplan.Testplan(
        name=six.ensure_str("InteractiveAPITest"),
        interactive_port=0,
        interactive_block=False,
        parse_cmdline=False,
    )
    plan.add(
        multitest.MultiTest(
            name=six.ensure_str("ExampleMTest"), suites=[ExampleSuite()]
        )
    )
    plan.run()
    timing.wait(
        lambda: plan.interactive.http_handler_info[0] is not None,
        300,
        raise_on_timeout=True,
    )
    yield plan
    plan.abort()


# Expected JSON to be returned from each API resource at start of day, before
# any tests have been run.
EXPECTED_INITIAL_GET = [
    (
        "/report",
        {
            "attachments": {},
            "category": "testplan",
            "entry_uids": ["ExampleMTest"],
            "meta": {},
            "name": "InteractiveAPITest",
            "parent_uids": [],
            "status": "ready",
            "status_override": None,
            "tags_index": {},
            "timer": {},
            "uid": "InteractiveAPITest",
        },
    ),
    (
        "/report/tests",
        [
            {
                "category": "multitest",
                "description": None,
                "entry_uids": ["ExampleSuite"],
                "fix_spec_path": None,
                "name": "ExampleMTest",
                "parent_uids": ["InteractiveAPITest"],
                "part": None,
                "status": "ready",
                "status_override": None,
                "tags": {},
                "timer": {},
                "uid": "ExampleMTest",
            }
        ],
    ),
    (
        "/report/tests/ExampleMTest",
        {
            "category": "multitest",
            "description": None,
            "entry_uids": ["ExampleSuite"],
            "fix_spec_path": None,
            "name": "ExampleMTest",
            "parent_uids": ["InteractiveAPITest"],
            "part": None,
            "status": "ready",
            "status_override": None,
            "tags": {},
            "timer": {},
            "uid": "ExampleMTest",
        },
    ),
    (
        "/report/tests/ExampleMTest/suites",
        [
            {
                "category": "suite",
                "description": None,
                "entry_uids": ["test_passes", "test_fails", "test_logs"],
                "fix_spec_path": None,
                "name": "ExampleSuite",
                "parent_uids": ["InteractiveAPITest", "ExampleMTest"],
                "part": None,
                "status": "ready",
                "status_override": None,
                "tags": {},
                "timer": {},
                "uid": "ExampleSuite",
            }
        ],
    ),
    (
        "/report/tests/ExampleMTest/suites/ExampleSuite",
        {
            "category": "suite",
            "description": None,
            "entry_uids": ["test_passes", "test_fails", "test_logs"],
            "fix_spec_path": None,
            "name": "ExampleSuite",
            "parent_uids": ["InteractiveAPITest", "ExampleMTest"],
            "part": None,
            "status": "ready",
            "status_override": None,
            "tags": {},
            "timer": {},
            "uid": "ExampleSuite",
        },
    ),
    (
        "/report/tests/ExampleMTest/suites/ExampleSuite/testcases",
        [
            {
                "category": "testcase",
                "description": None,
                "entries": [],
                "logs": [],
                "name": "test_passes",
                "parent_uids": [
                    "InteractiveAPITest",
                    "ExampleMTest",
                    "ExampleSuite",
                ],
                "status": "ready",
                "status_override": None,
                "suite_related": False,
                "tags": {},
                "timer": {},
                "type": "TestCaseReport",
                "uid": "test_passes",
            },
            {
                "category": "testcase",
                "description": None,
                "entries": [],
                "logs": [],
                "name": "test_fails",
                "parent_uids": [
                    "InteractiveAPITest",
                    "ExampleMTest",
                    "ExampleSuite",
                ],
                "status": "ready",
                "status_override": None,
                "suite_related": False,
                "tags": {},
                "timer": {},
                "type": "TestCaseReport",
                "uid": "test_fails",
            },
            {
                "category": "testcase",
                "description": None,
                "entries": [],
                "logs": [],
                "name": "test_logs",
                "parent_uids": [
                    "InteractiveAPITest",
                    "ExampleMTest",
                    "ExampleSuite",
                ],
                "status": "ready",
                "status_override": None,
                "suite_related": False,
                "tags": {},
                "timer": {},
                "type": "TestCaseReport",
                "uid": "test_logs",
            },
        ],
    ),
    (
        "/report/tests/ExampleMTest/suites/ExampleSuite/testcases/test_passes",
        {
            "category": "testcase",
            "description": None,
            "entries": [],
            "logs": [],
            "name": "test_passes",
            "parent_uids": [
                "InteractiveAPITest",
                "ExampleMTest",
                "ExampleSuite",
            ],
            "status": "ready",
            "status_override": None,
            "suite_related": False,
            "tags": {},
            "timer": {},
            "type": "TestCaseReport",
            "uid": "test_passes",
        },
    ),
]


# Expected results of testcases.
EXPECTED_TESTCASE_RESULTS = [
    ("test_passes", "passed"),
    ("test_fails", "failed"),
    ("test_logs", "passed"),
]


def test_initial_get(plan):
    """
    Test GETting the report state through each of the API resources at the
    start of day, i.e. before any tests have been run.
    """
    host, port = plan.interactive.http_handler_info
    assert host == "0.0.0.0"

    for resource_path, expected_json in EXPECTED_INITIAL_GET:
        rsp = requests.get(
            "http://localhost:{port}/api/v1/interactive{resource}".format(
                port=port, resource=resource_path
            )
        )
        assert rsp.status_code == 200
        test_api.compare_json(rsp.json(), expected_json)


def test_run_all_tests(plan):
    """
    Test running all tests.
    """
    host, port = plan.interactive.http_handler_info
    assert host == "0.0.0.0"

    report_url = "http://localhost:{}/api/v1/interactive/report".format(port)
    rsp = requests.get(report_url)
    assert rsp.status_code == 200
    report_json = rsp.json()
    last_hash = report_json["hash"]

    # Trigger all tests to run by updating the report status to RUNNING
    # and PUTting back the data.
    report_json["status"] = report.Status.RUNNING
    rsp = requests.put(report_url, json=report_json)
    assert rsp.status_code == 200

    updated_json = rsp.json()
    test_api.compare_json(updated_json, report_json)
    assert updated_json["hash"] != last_hash

    timing.wait(
        functools.partial(
            _check_test_status, report_url, "failed", updated_json["hash"]
        ),
        interval=0.2,
        timeout=300,
        raise_on_timeout=True,
    )


def test_run_mtest(plan):
    """Test running a single MultiTest."""
    host, port = plan.interactive.http_handler_info
    assert host == "0.0.0.0"

    mtest_url = "http://localhost:{}/api/v1/interactive/report/tests/ExampleMTest".format(
        port
    )
    rsp = requests.get(mtest_url)
    assert rsp.status_code == 200
    mtest_json = rsp.json()

    # Trigger all tests to run by updating the report status to RUNNING
    # and PUTting back the data.
    mtest_json["status"] = report.Status.RUNNING
    rsp = requests.put(mtest_url, json=mtest_json)
    assert rsp.status_code == 200
    updated_json = rsp.json()
    test_api.compare_json(updated_json, mtest_json)
    assert updated_json["hash"] != mtest_json["hash"]

    timing.wait(
        functools.partial(
            _check_test_status, mtest_url, "failed", updated_json["hash"]
        ),
        interval=0.2,
        timeout=300,
        raise_on_timeout=True,
    )


def test_run_suite(plan):
    """Test running a single test suite."""
    host, port = plan.interactive.http_handler_info
    assert host == "0.0.0.0"

    suite_url = (
        "http://localhost:{}/api/v1/interactive/report/tests/ExampleMTest/"
        "suites/ExampleSuite".format(port)
    )
    rsp = requests.get(suite_url)
    assert rsp.status_code == 200
    suite_json = rsp.json()

    # Trigger all tests to run by updating the report status to RUNNING
    # and PUTting back the data.
    suite_json["status"] = report.Status.RUNNING
    rsp = requests.put(suite_url, json=suite_json)
    assert rsp.status_code == 200
    updated_json = rsp.json()
    test_api.compare_json(updated_json, suite_json)
    assert updated_json["hash"] != suite_json["hash"]

    timing.wait(
        functools.partial(
            _check_test_status, suite_url, "failed", updated_json["hash"]
        ),
        interval=0.2,
        timeout=300,
        raise_on_timeout=True,
    )


def test_run_testcase(plan):
    """Test running a single testcase."""
    host, port = plan.interactive.http_handler_info
    assert host == "0.0.0.0"

    for testcase_name, expected_result in EXPECTED_TESTCASE_RESULTS:
        testcase_url = (
            "http://localhost:{port}/api/v1/interactive/report/tests/"
            "ExampleMTest/suites/ExampleSuite/testcases/{testcase}".format(
                port=port, testcase=testcase_name
            )
        )

        rsp = requests.get(testcase_url)
        assert rsp.status_code == 200
        testcase_json = rsp.json()

        # Trigger all tests to run by updating the report status to RUNNING
        # and PUTting back the data.
        testcase_json["status"] = report.Status.RUNNING
        rsp = requests.put(testcase_url, json=testcase_json)
        assert rsp.status_code == 200
        updated_json = rsp.json()
        test_api.compare_json(updated_json, testcase_json)
        assert updated_json["hash"] != testcase_json["hash"]

        timing.wait(
            functools.partial(
                _check_test_status,
                testcase_url,
                expected_result,
                updated_json["hash"],
            ),
            interval=0.2,
            timeout=300,
            raise_on_timeout=True,
        )


def _check_test_status(test_url, expected_status, last_hash):
    """
    Check the test status by polling the report resource. If the test is
    still running, return False. Otherwise assert that the status matches
    the expected status and return True.
    """
    rsp = requests.get(test_url)
    assert rsp.status_code == 200
    report_json = rsp.json()

    if report_json["status"] == report.Status.RUNNING:
        return False
    else:
        assert report_json["status"] == expected_status
        assert report_json["hash"] != last_hash
        return True
