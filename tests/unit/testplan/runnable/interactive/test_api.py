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
                category="multitest",
                entries=[
                    report.TestGroupReport(
                        name="Suite1",
                        uid="MT1Suite1",
                        category="suite",
                        entries=[
                            report.TestCaseReport(
                                name="TestCase1", uid="MT1S1TC1"
                            )
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
        assert rsp.status == "200 OK"
        json_rsp = rsp.get_json()
        assert json_rsp["status"] == "ready"
        assert json_rsp == json_report

    def test_put(self, api_env):
        """Test updating the Report resource via PUT."""
        client, ihandler = api_env

        json_report = ihandler.report.shallow_serialize()
        json_report["status"] = "running"
        rsp = client.put("/api/v1/interactive/report", json=json_report)
        assert rsp.status == "200 OK"
        rsp_json = rsp.get_json()
        assert rsp_json["status"] == "running"
        assert rsp_json == json_report
        ihandler.run_all_tests.assert_called_once_with(await_results=False)

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, _ = api_env

        # JSON body is required.
        rsp = client.put("/api/v1/interactive/report")
        assert rsp.status == "400 BAD REQUEST"

        # "uid" field is required.
        rsp = client.put(
            "/api/v1/interactive/report", json={"name": "ReportName"}
        )
        assert rsp.status == "400 BAD REQUEST"


class TestAllTests(object):
    """Test the AllTests resource."""

    def test_get(self, api_env):
        """Test reading the AllTests resource via GET."""
        client, ihandler = api_env
        rsp = client.get("/api/v1/interactive/report/tests")
        assert rsp.status == "200 OK"
        json_rsp = rsp.get_json()
        json_tests = [test.shallow_serialize() for test in ihandler.report]
        assert json_rsp == json_tests

    def test_put(self, api_env):
        """
        Test attempting to update the AllTests resource via PUT. This resource
        is read-only so PUT is not allowed.
        """
        client, _ = api_env
        rsp = client.put("/api/v1/interactive/report/tests")
        assert rsp.status == "405 METHOD NOT ALLOWED"


class TestSingleTest(object):
    """Test the SingleTest resource."""

    def test_get(self, api_env):
        """Test reading the SingleTest resource via GET."""
        client, ihandler = api_env
        rsp = client.get("/api/v1/interactive/report/tests/MTest1")
        assert rsp.status == "200 OK"

        json_rsp = rsp.get_json()
        json_test = ihandler.report["MTest1"].shallow_serialize()
        assert json_rsp == json_test

    def test_put(self, api_env):
        """Test updating the SingleTest resource via PUT."""
        client, ihandler = api_env

        json_test = ihandler.report["MTest1"].shallow_serialize()
        json_test["status"] = "running"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1", json=json_test
        )
        assert rsp.status == "200 OK"
        assert rsp.get_json() == json_test

        ihandler.run_test.assert_called_once_with(
            "MTest1", await_results=False
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, _ = api_env

        # JSON body is required.
        rsp = client.put("/api/v1/interactive/report/tests/MTest1")
        assert rsp.status == "400 BAD REQUEST"

        # "uid" field is required.
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1",
            json={"name": "MTestName"},
        )
        assert rsp.status == "400 BAD REQUEST"


class TestAllSuites(object):
    """Test the AllSuites resource."""

    def test_get(self, api_env):
        """Test reading the AllSuites resource via GET."""
        client, ihandler = api_env
        rsp = client.get("/api/v1/interactive/report/tests/MTest1/suites")
        assert rsp.status == "200 OK"
        json_rsp = rsp.get_json()
        json_suites = [
            suite.shallow_serialize() for suite in ihandler.report["MTest1"]
        ]
        assert json_rsp == json_suites

    def test_put(self, api_env):
        """
        Test attempting to update the AllSuites resource via PUT. This resource
        is read-only so PUT is not allowed.
        """
        client, _ = api_env
        rsp = client.put("/api/v1/interactive/report/tests/MTest1/suites")
        assert rsp.status == "405 METHOD NOT ALLOWED"


class TestSingleSuite(object):
    """Test the SingleSuite resource."""

    def test_get(self, api_env):
        """Test reading the SingleSuite resource via GET."""
        client, ihandler = api_env
        rsp = client.get(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1"
        )
        assert rsp.status == "200 OK"

        json_rsp = rsp.get_json()
        suite_json = ihandler.report["MTest1"]["MT1Suite1"].shallow_serialize()
        assert json_rsp == suite_json

    def test_put(self, api_env):
        """Test updating the SingleSuite resource via PUT."""
        client, ihandler = api_env

        suite_json = ihandler.report["MTest1"]["MT1Suite1"].shallow_serialize()
        suite_json["status"] = "running"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1",
            json=suite_json,
        )
        assert rsp.status == "200 OK"
        assert rsp.get_json() == suite_json

        ihandler.run_test_suite.assert_called_once_with(
            "MTest1", "MT1Suite1", await_results=False
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, _ = api_env

        # JSON body is required.
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1"
        )
        assert rsp.status == "400 BAD REQUEST"

        # "uid" field is required.
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1",
            json={"name": "SuiteName"},
        )
        assert rsp.status == "400 BAD REQUEST"


class TestAllTestcases(object):
    """Test the Testcases resource."""

    def test_get(self, api_env):
        """Test reading the AllTestcases resource via GET."""
        client, ihandler = api_env
        rsp = client.get(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/testcases"
        )
        assert rsp.status == "200 OK"
        json_rsp = rsp.get_json()
        json_testcases = [
            testcase.serialize()
            for testcase in ihandler.report["MTest1"]["MT1Suite1"]
        ]
        assert json_rsp == json_testcases

    def test_put(self, api_env):
        """
        Test attempting to update the AllTestcases resource via PUT. This
        resource is read-only so PUT is not allowed.
        """
        client, _ = api_env
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/testcases"
        )
        assert rsp.status == "405 METHOD NOT ALLOWED"


class TestSingleTestcase(object):
    """Test the SingleTestcase resource."""

    def test_get(self, api_env):
        """Test reading the SingleTestcase resource via GET."""
        client, ihandler = api_env
        rsp = client.get(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/testcases/"
            "MT1S1TC1"
        )
        assert rsp.status == "200 OK"

        json_rsp = rsp.get_json()
        testcase_json = ihandler.report["MTest1"]["MT1Suite1"][
            "MT1S1TC1"
        ].serialize()
        assert json_rsp == testcase_json

    def test_put(self, api_env):
        """Test updating the SingleTestcase resource via PUT."""
        client, ihandler = api_env

        testcase_json = ihandler.report["MTest1"]["MT1Suite1"][
            "MT1S1TC1"
        ].serialize()
        testcase_json["status"] = "running"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/testcases/"
            "MT1S1TC1",
            json=testcase_json,
        )
        assert rsp.status == "200 OK"
        assert rsp.get_json() == testcase_json

        ihandler.run_test_case.assert_called_once_with(
            "MTest1", "MT1Suite1", "MT1S1TC1", await_results=False
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, _ = api_env

        # JSON body is required.
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/"
            "testcases/MT1S1TC1"
        )
        assert rsp.status == "400 BAD REQUEST"

        # "uid" field is required.
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/"
            "testcases/MT1S1TC1",
            json={"name": "TestcaseName"},
        )
        assert rsp.status == "400 BAD REQUEST"
