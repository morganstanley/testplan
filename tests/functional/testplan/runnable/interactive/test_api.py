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
from testplan.common import entity

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

    @multitest.testcase(parameters=[1, 2, 3])
    def test_parametrized(self, env, result, val):
        """Parametrized testcase."""
        result.log(val)
        result.gt(val, 0)
        result.lt(val, 10)


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
        lambda: plan.interactive.http_handler_info is not None,
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
            "status": "unknown",
            "runtime_status": "ready",
            "counter": {"failed": 0, "passed": 0, "total": 6, "unknown": 6},
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
                "env_status": "STOPPED",
                "fix_spec_path": None,
                "name": "ExampleMTest",
                "parent_uids": ["InteractiveAPITest"],
                "part": None,
                "status": "unknown",
                "runtime_status": "ready",
                "counter": {
                    "failed": 0,
                    "passed": 0,
                    "total": 6,
                    "unknown": 6,
                },
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
            "env_status": "STOPPED",
            "fix_spec_path": None,
            "name": "ExampleMTest",
            "parent_uids": ["InteractiveAPITest"],
            "part": None,
            "status": "unknown",
            "runtime_status": "ready",
            "counter": {"failed": 0, "passed": 0, "total": 6, "unknown": 6},
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
                "category": "testsuite",
                "description": "Example test suite.",
                "entry_uids": [
                    "test_passes",
                    "test_fails",
                    "test_logs",
                    "test_parametrized",
                ],
                "env_status": None,
                "fix_spec_path": None,
                "name": "ExampleSuite",
                "parent_uids": ["InteractiveAPITest", "ExampleMTest"],
                "part": None,
                "status": "unknown",
                "runtime_status": "ready",
                "counter": {
                    "failed": 0,
                    "passed": 0,
                    "total": 6,
                    "unknown": 6,
                },
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
            "category": "testsuite",
            "description": "Example test suite.",
            "entry_uids": [
                "test_passes",
                "test_fails",
                "test_logs",
                "test_parametrized",
            ],
            "env_status": None,
            "fix_spec_path": None,
            "name": "ExampleSuite",
            "parent_uids": ["InteractiveAPITest", "ExampleMTest"],
            "part": None,
            "status": "unknown",
            "runtime_status": "ready",
            "counter": {"failed": 0, "passed": 0, "total": 6, "unknown": 6},
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
                "description": "Testcase that passes.",
                "entries": [],
                "logs": [],
                "name": "test_passes",
                "parent_uids": [
                    "InteractiveAPITest",
                    "ExampleMTest",
                    "ExampleSuite",
                ],
                "status": "unknown",
                "runtime_status": "ready",
                "counter": {
                    "passed": 0,
                    "failed": 0,
                    "total": 1,
                    "unknown": 1,
                },
                "status_override": None,
                "suite_related": False,
                "tags": {},
                "timer": {},
                "type": "TestCaseReport",
                "uid": "test_passes",
                "status_reason": None,
            },
            {
                "category": "testcase",
                "description": "Testcase that fails.",
                "entries": [],
                "logs": [],
                "name": "test_fails",
                "parent_uids": [
                    "InteractiveAPITest",
                    "ExampleMTest",
                    "ExampleSuite",
                ],
                "status": "unknown",
                "runtime_status": "ready",
                "counter": {
                    "passed": 0,
                    "failed": 0,
                    "total": 1,
                    "unknown": 1,
                },
                "status_override": None,
                "suite_related": False,
                "tags": {},
                "timer": {},
                "type": "TestCaseReport",
                "uid": "test_fails",
                "status_reason": None,
            },
            {
                "category": "testcase",
                "description": "Testcase that makes a log.",
                "entries": [],
                "logs": [],
                "name": "test_logs",
                "parent_uids": [
                    "InteractiveAPITest",
                    "ExampleMTest",
                    "ExampleSuite",
                ],
                "status": "unknown",
                "runtime_status": "ready",
                "status_override": None,
                "counter": {
                    "passed": 0,
                    "failed": 0,
                    "total": 1,
                    "unknown": 1,
                },
                "suite_related": False,
                "tags": {},
                "timer": {},
                "type": "TestCaseReport",
                "uid": "test_logs",
                "status_reason": None,
            },
            {
                "category": "parametrization",
                "counter": {
                    "passed": 0,
                    "failed": 0,
                    "total": 3,
                    "unknown": 3,
                },
                "description": None,
                "entry_uids": [
                    "test_parametrized__val_1",
                    "test_parametrized__val_2",
                    "test_parametrized__val_3",
                ],
                "env_status": None,
                "fix_spec_path": None,
                "name": "test_parametrized",
                "parent_uids": [
                    "InteractiveAPITest",
                    "ExampleMTest",
                    "ExampleSuite",
                ],
                "part": None,
                "runtime_status": "ready",
                "status": "unknown",
                "status_override": None,
                "tags": {},
                "timer": {},
                "uid": "test_parametrized",
            },
        ],
    ),
    (
        "/report/tests/ExampleMTest/suites/ExampleSuite/testcases/test_passes",
        {
            "category": "testcase",
            "description": "Testcase that passes.",
            "entries": [],
            "logs": [],
            "name": "test_passes",
            "parent_uids": [
                "InteractiveAPITest",
                "ExampleMTest",
                "ExampleSuite",
            ],
            "status": "unknown",
            "runtime_status": "ready",
            "status_override": None,
            "suite_related": False,
            "tags": {},
            "timer": {},
            "type": "TestCaseReport",
            "uid": "test_passes",
            "status_reason": None,
        },
    ),
    (
        "/report/tests/ExampleMTest/suites/ExampleSuite/testcases/"
        "test_parametrized/parametrizations",
        [
            {
                "category": "testcase",
                "description": "Parametrized testcase.",
                "entries": [],
                "logs": [],
                "name": "test_parametrized__val_1",
                "parent_uids": [
                    "InteractiveAPITest",
                    "ExampleMTest",
                    "ExampleSuite",
                    "test_parametrized",
                ],
                "status": "unknown",
                "runtime_status": "ready",
                "status_override": None,
                "suite_related": False,
                "tags": {},
                "timer": {},
                "type": "TestCaseReport",
                "uid": "test_parametrized__val_1",
                "status_reason": None,
            },
            {
                "category": "testcase",
                "description": "Parametrized testcase.",
                "entries": [],
                "logs": [],
                "name": "test_parametrized__val_2",
                "parent_uids": [
                    "InteractiveAPITest",
                    "ExampleMTest",
                    "ExampleSuite",
                    "test_parametrized",
                ],
                "status": "unknown",
                "runtime_status": "ready",
                "status_override": None,
                "suite_related": False,
                "tags": {},
                "timer": {},
                "type": "TestCaseReport",
                "uid": "test_parametrized__val_2",
                "status_reason": None,
            },
            {
                "category": "testcase",
                "description": "Parametrized testcase.",
                "entries": [],
                "logs": [],
                "name": "test_parametrized__val_3",
                "parent_uids": [
                    "InteractiveAPITest",
                    "ExampleMTest",
                    "ExampleSuite",
                    "test_parametrized",
                ],
                "status": "unknown",
                "runtime_status": "ready",
                "status_override": None,
                "suite_related": False,
                "tags": {},
                "timer": {},
                "type": "TestCaseReport",
                "uid": "test_parametrized__val_3",
                "status_reason": None,
            },
        ],
    ),
    (
        "/report/tests/ExampleMTest/suites/ExampleSuite/testcases/"
        "test_parametrized/parametrizations/test_parametrized__val_1",
        {
            "category": "testcase",
            "description": "Parametrized testcase.",
            "entries": [],
            "logs": [],
            "name": "test_parametrized__val_1",
            "parent_uids": [
                "InteractiveAPITest",
                "ExampleMTest",
                "ExampleSuite",
                "test_parametrized",
            ],
            "status": "unknown",
            "runtime_status": "ready",
            "status_override": None,
            "suite_related": False,
            "tags": {},
            "timer": {},
            "type": "TestCaseReport",
            "uid": "test_parametrized__val_1",
            "status_reason": None,
        },
    ),
]


# Expected results of testcases.
EXPECTED_TESTCASE_RESULTS = [
    ("test_passes", "passed"),
    ("test_fails", "failed"),
    ("test_logs", "passed"),
    ("test_parametrized", "passed"),
]

# Expected results of parametrized testcases.
EXPECTED_PARAM_TESTCASE_RESULTS = [
    ("test_parametrized__val_1", "passed"),
    ("test_parametrized__val_2", "passed"),
    ("test_parametrized__val_3", "passed"),
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
    report_json["runtime_status"] = report.RuntimeStatus.RUNNING
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
    mtest_json["runtime_status"] = report.RuntimeStatus.RUNNING
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


def test_environment_control(plan):
    """Test starting and stopping the environment."""
    host, port = plan.interactive.http_handler_info
    assert host == "0.0.0.0"

    mtest_url = "http://localhost:{}/api/v1/interactive/report/tests/ExampleMTest".format(
        port
    )
    rsp = requests.get(mtest_url)
    assert rsp.status_code == 200
    mtest_json = rsp.json()

    # Trigger the environment to start by setting the env_status to STARTING
    # and PUTting back the data.
    mtest_json["env_status"] = entity.ResourceStatus.STARTING
    rsp = requests.put(mtest_url, json=mtest_json)
    assert rsp.status_code == 200
    updated_json = rsp.json()
    test_api.compare_json(updated_json, mtest_json)
    assert updated_json["hash"] != mtest_json["hash"]

    # Wait for the environment to become STARTED.
    timing.wait(
        functools.partial(
            _check_env_status,
            mtest_url,
            entity.ResourceStatus.STARTED,
            updated_json["hash"],
        ),
        interval=0.2,
        timeout=300,
        raise_on_timeout=True,
    )

    # Now trigger the environment to stop by setting the env_status to STOPPING
    # and PUTting back the data.
    mtest_json = updated_json
    mtest_json["env_status"] = entity.ResourceStatus.STOPPING
    rsp = requests.put(mtest_url, json=mtest_json)
    assert rsp.status_code == 200
    updated_json = rsp.json()
    test_api.compare_json(updated_json, mtest_json)
    assert updated_json["hash"] != mtest_json["hash"]

    # Wait for the environment to become STOPPED.
    timing.wait(
        functools.partial(
            _check_env_status,
            mtest_url,
            entity.ResourceStatus.STOPPED,
            updated_json["hash"],
        ),
        interval=0.2,
        timeout=30,
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
    suite_json["runtime_status"] = report.RuntimeStatus.RUNNING
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
        testcase_json["runtime_status"] = report.RuntimeStatus.RUNNING
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


def test_run_param_testcase(plan):
    """Test running a single parametrized testcase."""
    host, port = plan.interactive.http_handler_info
    assert host == "0.0.0.0"

    for param_name, expected_result in EXPECTED_PARAM_TESTCASE_RESULTS:
        testcase_url = (
            "http://localhost:{port}/api/v1/interactive/report/tests/"
            "ExampleMTest/suites/ExampleSuite/testcases/test_parametrized/"
            "parametrizations/{param}".format(port=port, param=param_name)
        )

        rsp = requests.get(testcase_url)
        assert rsp.status_code == 200
        testcase_json = rsp.json()

        # Trigger all tests to run by updating the report status to RUNNING
        # and PUTting back the data.
        testcase_json["runtime_status"] = report.RuntimeStatus.RUNNING
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

    if report_json["runtime_status"] == report.RuntimeStatus.RUNNING:
        return False
    else:
        assert report_json["runtime_status"] == report.RuntimeStatus.FINISHED
        assert report_json["status"] == expected_status
        assert report_json["hash"] != last_hash
        return True


def _check_env_status(test_url, expected_status, last_hash):
    """
    Check the environment status by polling the report resource. Return
    True if the status matches the expected status, False otherwise.
    """
    rsp = requests.get(test_url)
    assert rsp.status_code == 200
    report_json = rsp.json()

    if report_json["env_status"] == expected_status:
        assert report_json["hash"] != last_hash
        return True
    else:
        return False
