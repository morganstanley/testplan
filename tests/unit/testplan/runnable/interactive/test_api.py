"""Test the interactive HTTP API."""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()
import mock
import pytest

from testplan.runnable.interactive import http
from testplan.runnable.interactive import base
from testplan import report
from testplan.common import entity


@pytest.fixture
def example_report():
    """Create a new report skeleton."""
    return report.TestReport(
        name="Interactive API Test",
        uid="Interactive API Test",
        entries=[
            report.TestGroupReport(
                name="MTest1",
                uid="MTest1",
                category=report.ReportCategories.MULTITEST,
                env_status=entity.ResourceStatus.STOPPED,
                parent_uids=["Interactive API Test"],
                entries=[
                    report.TestGroupReport(
                        name="Suite1",
                        uid="MT1Suite1",
                        category=report.ReportCategories.TESTSUITE,
                        parent_uids=["Interactive API Test", "MTest1"],
                        entries=[
                            report.TestCaseReport(
                                name="TestCase1",
                                uid="MT1S1TC1",
                                parent_uids=[
                                    "Interactive API Test",
                                    "MTest1",
                                    "MT1Suite1",
                                ],
                            ),
                            report.TestGroupReport(
                                name="ParametrizedTestCase",
                                uid="MT1S1TC2",
                                category=(
                                    report.ReportCategories.PARAMETRIZATION
                                ),
                                parent_uids=[
                                    "Interactive API Test",
                                    "MTest1",
                                    "MT1Suite1",
                                ],
                                entries=[
                                    report.TestCaseReport(
                                        name="ParametrizedTestCase_0",
                                        uid="MT1S1TC2_0",
                                        parent_uids=[
                                            "Interactive API Test",
                                            "MTest1",
                                            "MT1Suite1",
                                            "MT1S1TC2",
                                        ],
                                    ),
                                    report.TestCaseReport(
                                        name="ParametrizedTestCase_1",
                                        uid="MT1S1TC2_1",
                                        parent_uids=[
                                            "Interactive API Test",
                                            "MTest1",
                                            "MT1Suite1",
                                            "MT1S1TC2",
                                        ],
                                    ),
                                    report.TestCaseReport(
                                        name="ParametrizedTestCase_2",
                                        uid="MT1S1TC2_2",
                                        parent_uids=[
                                            "Interactive API Test",
                                            "MTest1",
                                            "MT1Suite1",
                                            "MT1S1TC2",
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            )
        ],
    )


@pytest.fixture()
def api_env(example_report):
    """
    Set up and yield a client object for the API and the interactive handler.
    """
    mock_target = mock.MagicMock()
    mock_target.cfg.name = "Interactive API Test"

    ihandler = base.TestRunnerIHandler(target=mock_target)
    ihandler.report = example_report
    ihandler.run_all_tests = mock.MagicMock()
    ihandler.run_test = mock.MagicMock()
    ihandler.run_test_suite = mock.MagicMock()
    ihandler.run_test_case = mock.MagicMock()
    ihandler.run_parametrized_test_case = mock.MagicMock()
    ihandler.start_test_resources = mock.MagicMock()
    ihandler.stop_test_resources = mock.MagicMock()

    app, _ = http.generate_interactive_api(ihandler)
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client, ihandler


class TestReport(object):
    """Test the Report resource."""

    def test_get(self, api_env):
        """Test reading the Report resource via GET."""
        client, ihandler = api_env

        json_report = ihandler.report.shallow_serialize()
        rsp = client.get("/api/v1/interactive/report")
        assert rsp.status_code == 200
        json_rsp = rsp.get_json()
        assert json_rsp["runtime_status"] == "ready"
        compare_json(json_rsp, json_report)

    def test_put(self, api_env):
        """Test updating the Report resource via PUT."""
        client, ihandler = api_env

        json_report = ihandler.report.shallow_serialize()
        json_report["runtime_status"] = "running"
        rsp = client.put("/api/v1/interactive/report", json=json_report)
        assert rsp.status_code == 200
        rsp_json = rsp.get_json()
        assert rsp_json["runtime_status"] == "running"
        compare_json(rsp_json, json_report)
        ihandler.run_all_tests.assert_called_once_with(await_results=False)

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, ihandler = api_env
        api_url = "/api/v1/interactive/report"

        # JSON body is required.
        rsp = client.put(api_url)
        assert rsp.status_code == 400

        # "uid" field is required.
        rsp = client.put(api_url, json={"name": "ReportName"})
        assert rsp.status_code == 400

        # "uid" field cannot be changed.
        shallow_report = ihandler.report.shallow_serialize()
        shallow_report["uid"] = "I have changed"
        rsp = client.put(api_url, json=shallow_report)
        assert rsp.status_code == 400


class TestAllTests(object):
    """Test the AllTests resource."""

    def test_get(self, api_env):
        """Test reading the AllTests resource via GET."""
        client, ihandler = api_env
        rsp = client.get("/api/v1/interactive/report/tests")
        assert rsp.status_code == 200
        json_rsp = rsp.get_json()
        json_tests = [test.shallow_serialize() for test in ihandler.report]
        compare_json(json_rsp, json_tests)

    def test_put(self, api_env):
        """
        Test attempting to update the AllTests resource via PUT. This resource
        is read-only so PUT is not allowed.
        """
        client, _ = api_env
        rsp = client.put("/api/v1/interactive/report/tests")
        assert rsp.status_code == 405


class TestSingleTest(object):
    """Test the SingleTest resource."""

    def test_get(self, api_env):
        """Test reading the SingleTest resource via GET."""
        client, ihandler = api_env
        rsp = client.get("/api/v1/interactive/report/tests/MTest1")
        assert rsp.status_code == 200

        json_rsp = rsp.get_json()
        json_test = ihandler.report["MTest1"].shallow_serialize()
        compare_json(json_rsp, json_test)

    def test_put(self, api_env):
        """Test updating the SingleTest resource via PUT."""
        client, ihandler = api_env

        json_test = ihandler.report["MTest1"].shallow_serialize()
        json_test["runtime_status"] = "running"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1", json=json_test
        )
        assert rsp.status_code == 200
        compare_json(rsp.get_json(), json_test)

        ihandler.run_test.assert_called_once_with(
            "MTest1", await_results=False
        )

    def test_put_env(self, api_env):
        """Test starting and stopping a test environment via PUT."""
        client, ihandler = api_env

        json_test = ihandler.report["MTest1"].shallow_serialize()
        json_test["env_status"] = "STARTING"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1", json=json_test
        )
        assert rsp.status_code == 200
        compare_json(rsp.get_json(), json_test)

        ihandler.start_test_resources.assert_called_once_with(
            "MTest1", await_results=False
        )

        # Mark the environment as STARTED and then request for it to stop.
        ihandler.report["MTest1"].env_status = "STARTED"
        json_test["env_status"] = "STOPPING"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1", json=json_test
        )
        assert rsp.status_code == 200
        compare_json(rsp.get_json(), json_test)

        ihandler.stop_test_resources.assert_called_once_with(
            "MTest1", await_results=False
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, ihandler = api_env
        api_url = "/api/v1/interactive/report/tests/MTest1"

        # JSON body is required.
        rsp = client.put(api_url)
        assert rsp.status_code == 400

        # "uid" field is required.
        rsp = client.put(api_url, json={"name": "MTestName"})
        assert rsp.status_code == 400

        # "uid" field cannot be changed.
        shallow_test = ihandler.report["MTest1"].shallow_serialize()
        shallow_test["uid"] = "I have changed"
        rsp = client.put(api_url, json=shallow_test)
        assert rsp.status_code == 400


class TestAllSuites(object):
    """Test the AllSuites resource."""

    def test_get(self, api_env):
        """Test reading the AllSuites resource via GET."""
        client, ihandler = api_env
        rsp = client.get("/api/v1/interactive/report/tests/MTest1/suites")
        assert rsp.status_code == 200
        json_rsp = rsp.get_json()
        json_suites = [
            suite.shallow_serialize() for suite in ihandler.report["MTest1"]
        ]
        compare_json(json_rsp, json_suites)

    def test_put(self, api_env):
        """
        Test attempting to update the AllSuites resource via PUT. This resource
        is read-only so PUT is not allowed.
        """
        client, _ = api_env
        rsp = client.put("/api/v1/interactive/report/tests/MTest1/suites")
        assert rsp.status_code == 405


class TestSingleSuite(object):
    """Test the SingleSuite resource."""

    def test_get(self, api_env):
        """Test reading the SingleSuite resource via GET."""
        client, ihandler = api_env
        rsp = client.get(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1"
        )
        assert rsp.status_code == 200

        json_rsp = rsp.get_json()
        suite_json = ihandler.report["MTest1"]["MT1Suite1"].shallow_serialize()
        compare_json(json_rsp, suite_json)

    def test_put(self, api_env):
        """Test updating the SingleSuite resource via PUT."""
        client, ihandler = api_env

        suite_json = ihandler.report["MTest1"]["MT1Suite1"].shallow_serialize()
        suite_json["runtime_status"] = "running"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1",
            json=suite_json,
        )
        assert rsp.status_code == 200
        compare_json(rsp.get_json(), suite_json)

        ihandler.run_test_suite.assert_called_once_with(
            "MTest1", "MT1Suite1", await_results=False
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, ihandler = api_env
        api_url = "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1"

        # JSON body is required.
        rsp = client.put(api_url)
        assert rsp.status_code == 400

        # "uid" field is required.
        rsp = client.put(api_url, json={"name": "SuiteName"})
        assert rsp.status_code == 400

        # "uid" field cannot be changed.
        shallow_suite = ihandler.report["MTest1"][
            "MT1Suite1"
        ].shallow_serialize()
        shallow_suite["uid"] = "I have changed"
        rsp = client.put(api_url, json=shallow_suite)
        assert rsp.status_code == 400


class TestAllTestcases(object):
    """Test the Testcases resource."""

    def test_get(self, api_env):
        """Test reading the AllTestcases resource via GET."""
        client, ihandler = api_env
        rsp = client.get(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/testcases"
        )
        assert rsp.status_code == 200
        json_rsp = rsp.get_json()
        json_testcases = [
            serialize_testcase(testcase)
            for testcase in ihandler.report["MTest1"]["MT1Suite1"]
        ]
        compare_json(json_rsp, json_testcases)

    def test_put(self, api_env):
        """
        Test attempting to update the AllTestcases resource via PUT. This
        resource is read-only so PUT is not allowed.
        """
        client, _ = api_env
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/testcases"
        )
        assert rsp.status_code == 405


class TestSingleTestcase(object):
    """Test the SingleTestcase resource."""

    @pytest.mark.parametrize("testcase_uid", ["MT1S1TC1", "MT1S1TC2"])
    def test_get(self, api_env, testcase_uid):
        """Test reading the SingleTestcase resource via GET."""
        client, ihandler = api_env
        rsp = client.get(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/"
            "testcases/{}".format(testcase_uid)
        )
        assert rsp.status_code == 200

        json_rsp = rsp.get_json()

        report_entry = ihandler.report["MTest1"]["MT1Suite1"][testcase_uid]

        if isinstance(report_entry, report.TestCaseReport):
            testcase_json = report_entry.serialize()
        elif isinstance(report_entry, report.TestGroupReport):
            testcase_json = report_entry.shallow_serialize()
        else:
            raise TypeError("Unexpected report type.")

        compare_json(json_rsp, testcase_json)

    @pytest.mark.parametrize("testcase_uid", ["MT1S1TC1", "MT1S1TC2"])
    def test_put(self, api_env, testcase_uid):
        """Test updating the SingleTestcase resource via PUT."""
        client, ihandler = api_env
        report_entry = ihandler.report["MTest1"]["MT1Suite1"][testcase_uid]

        if isinstance(report_entry, report.TestCaseReport):
            testcase_json = report_entry.serialize()
        elif isinstance(report_entry, report.TestGroupReport):
            testcase_json = report_entry.shallow_serialize()
        else:
            raise TypeError("Unexpected report type")

        testcase_json["runtime_status"] = "running"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/"
            "testcases/{}".format(testcase_uid),
            json=testcase_json,
        )
        assert rsp.status_code == 200
        compare_json(rsp.get_json(), testcase_json)

        ihandler.run_test_case.assert_called_once_with(
            "MTest1", "MT1Suite1", testcase_uid, await_results=False
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, ihandler = api_env
        api_url = (
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/"
            "testcases/MT1S1TC1"
        )

        # JSON body is required.
        rsp = client.put(api_url)
        assert rsp.status_code == 400

        # "uid" field is required.
        rsp = client.put(api_url, json={"name": "TestcaseName"})
        assert rsp.status_code == 400

        # "uid" field cannot be changed.
        serialized_testcase = ihandler.report["MTest1"]["MT1Suite1"][
            "MT1S1TC1"
        ].serialize()
        serialized_testcase["uid"] = "I have changed"
        rsp = client.put(api_url, json=serialized_testcase)
        assert rsp.status_code == 400


class TestAllParametrizations(object):
    """Test the AllParametrizations resource."""

    def test_get(self, api_env):
        """Test reading the AllParametrizations resource via GET."""
        client, ihandler = api_env
        rsp = client.get(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/"
            "testcases/MT1S1TC2/parametrizations"
        )
        assert rsp.status_code == 200
        json_rsp = rsp.get_json()
        json_parametrizations = [
            param.serialize()
            for param in ihandler.report["MTest1"]["MT1Suite1"]["MT1S1TC2"]
        ]
        compare_json(json_rsp, json_parametrizations)

    def test_put(self, api_env):
        """
        Test attempting to update the AllParametrizations resource via PUT.
        This resource is read-only so PUT is not allowed.
        """
        client, _ = api_env
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/"
            "testcases/MT1S1TC2/parametrizations"
        )
        assert rsp.status_code == 405


class TestParametrizedTestCase(object):
    """Test the ParametrizedTestCase resource."""

    def test_get(self, api_env):
        """Test reading the ParametrizedTestCase resource via GET."""
        client, ihandler = api_env
        rsp = client.get(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/"
            "testcases/MT1S1TC2/parametrizations/MT1S1TC2_0"
        )
        assert rsp.status_code == 200

        json_rsp = rsp.get_json()

        report_entry = ihandler.report["MTest1"]["MT1Suite1"]["MT1S1TC2"][
            "MT1S1TC2_0"
        ]

        testcase_json = report_entry.serialize()
        compare_json(json_rsp, testcase_json)

    def test_put(self, api_env):
        """Test updating the ParametrizedTestCase resource via PUT."""
        client, ihandler = api_env
        report_entry = ihandler.report["MTest1"]["MT1Suite1"]["MT1S1TC2"][
            "MT1S1TC2_0"
        ]
        testcase_json = report_entry.serialize()

        testcase_json["runtime_status"] = "running"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/"
            "testcases/MT1S1TC2/parametrizations/MT1S1TC2_0",
            json=testcase_json,
        )
        assert rsp.status_code == 200
        compare_json(rsp.get_json(), testcase_json)

        ihandler.run_test_case.assert_called_once_with(
            "MTest1", "MT1Suite1", "MT1S1TC2_0", await_results=False
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, ihandler = api_env
        api_url = (
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/"
            "testcases/MT1S1TC2/parametrizations/MT1S1TC2_0"
        )

        # JSON body is required.
        rsp = client.put(api_url)
        assert rsp.status_code == 400

        # "uid" field is required.
        rsp = client.put(api_url, json={"name": "TestcaseName"})
        assert rsp.status_code == 400

        # "uid" field cannot be changed.
        serialized_testcase = ihandler.report["MTest1"]["MT1Suite1"][
            "MT1S1TC2"
        ]["MT1S1TC2_0"].serialize()
        serialized_testcase["uid"] = "I have changed"
        rsp = client.put(api_url, json=serialized_testcase)
        assert rsp.status_code == 400


def compare_json(actual, expected):
    """
    Compare the actual and expected JSON returned from the API. Since the
    JSON contains a hash value we cannot predict, we cannot simply check
    for exact equality against a reference.
    """
    if isinstance(actual, list):
        assert isinstance(expected, list)
        for actual_item, expected_item in zip(actual, expected):
            compare_json(actual_item, expected_item)
    else:
        assert isinstance(actual, dict)
        assert isinstance(expected, dict)

        for key in expected:
            # Skip checking the "hash" key.
            if key != "hash":
                assert actual[key] == expected[key]


def serialize_testcase(testcase):
    """
    Serialize a testcase.

    If the testcase contains parametrizations, it will be represented as a
    TestGroupReport in the report tree and should be shallow-serialized.
    Otherwise, for a regular testcase we serialize the whole thing including
    its entries.
    """
    if isinstance(testcase, report.TestCaseReport):
        return testcase.serialize()
    elif isinstance(testcase, report.TestGroupReport):
        return testcase.shallow_serialize()
    else:
        raise TypeError("Unexpected testcase type: {}".format(type(testcase)))
