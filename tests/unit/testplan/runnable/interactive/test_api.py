"""Test the interactive HTTP API."""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()
import mock
import json
import copy

import pytest

from testplan.runnable.interactive import http
from testplan.runnable.interactive import base
from testplan import report


@pytest.fixture
def example_report():
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
    mock_target = mock.MagicMock()
    mock_target.cfg.name = "Interactive API Test"

    ihandler = base.TestRunnerIHandler(target=mock_target)
    ihandler.report = example_report

    mock_httphandler = mock.MagicMock()

    app, _ = http.generate_interactive_api(mock_httphandler, ihandler)
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client, mock_httphandler, ihandler


class TestReport(object):
    """Test the Report resource."""

    def test_get(self, api_env):
        """Test reading the Report resource via GET."""
        client, mock_httphandler, ihandler = api_env

        json_report = ihandler.report.shallow_serialize()
        rsp = client.get("/api/v1/interactive/report")
        assert rsp.status == "200 OK"
        json_rsp = rsp.get_json()
        assert json_rsp["status"] == "ready"
        assert json_rsp == json_report

    def test_put(self, api_env):
        """Test updating the Report resource via PUT."""
        client, mock_httphandler, ihandler = api_env

        json_report = ihandler.report.shallow_serialize()
        json_report["status"] = "running"
        rsp = client.put("/api/v1/interactive/report", json=json_report)
        assert rsp.status == "200 OK"
        rsp_json = rsp.get_json()
        assert rsp_json["status"] == "running"
        assert rsp_json == json_report
        mock_httphandler.pool.apply_async.assert_called_once_with(
            ihandler.run_tests
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, _, _ = api_env

        # JSON body is required.
        rsp = client.put("/api/v1/interactive/report")
        assert rsp.status == "400 BAD REQUEST"

        # "uid" field is required.
        rsp = client.put(
            "/api/v1/interactive/report", json={"name": "ReportName"}
        )
        assert rsp.status == "400 BAD REQUEST"


class TestTests(object):
    """Test the Tests resource."""

    def test_get(self, api_env):
        """Test reading the Tests resource via GET."""
        client, _, _ = api_env
        rsp = client.get("/api/v1/interactive/report/tests")
        assert rsp.status == "200 OK"
        json_rsp = rsp.get_json()
        assert json_rsp == ["MTest1"]

    def test_put(self, api_env):
        """
        Test attempting to update the Tests resource via PUT. This resource
        is read-only so PUT is not allowed.
        """
        client, _, _ = api_env
        rsp = client.put("/api/v1/interactive/report/tests")
        assert rsp.status == "405 METHOD NOT ALLOWED"


class TestTest(object):
    """Test the Test endpoint."""

    def test_get(self, api_env):
        """Test reading the Test resource via GET."""
        client, mock_httphandler, ihandler = api_env
        rsp = client.get("/api/v1/interactive/report/tests/MTest1")
        assert rsp.status == "200 OK"

        json_rsp = rsp.get_json()
        json_test = ihandler.report["MTest1"].shallow_serialize()
        assert json_rsp == json_test

    def test_put(self, api_env):
        """Test updating the Test resource via PUT."""
        client, mock_httphandler, ihandler = api_env

        json_test = ihandler.report["MTest1"].shallow_serialize()
        json_test["status"] = "running"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1", json=json_test
        )
        assert rsp.status == "200 OK"
        assert rsp.get_json() == json_test

        mock_httphandler.pool.apply_async.assert_called_once_with(
            ihandler.run_test, ("MTest1",)
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, _, _ = api_env

        # JSON body is required.
        rsp = client.put("/api/v1/interactive/report/tests/MTest1")
        assert rsp.status == "400 BAD REQUEST"

        # "uid" field is required.
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1",
            json={"name": "MTestName"},
        )
        assert rsp.status == "400 BAD REQUEST"


class TestSuites(object):
    """Test the Suites resource."""

    def test_get(self, api_env):
        """Test reading the Suites resource via GET."""
        client, _, _ = api_env
        rsp = client.get("/api/v1/interactive/report/tests/MTest1/suites")
        assert rsp.status == "200 OK"
        json_rsp = rsp.get_json()
        assert json_rsp == ["MT1Suite1"]

    def test_put(self, api_env):
        """
        Test attempting to update the Suites resource via PUT. This resource is
        read-only so PUT is not allowed.
        """
        client, _, _ = api_env
        rsp = client.put("/api/v1/interactive/report/tests/MTest1/suites")
        assert rsp.status == "405 METHOD NOT ALLOWED"


class TestSuite(object):
    """Test the Suite resource."""

    def test_get(self, api_env):
        """Test reading the Suite resource via GET."""
        client, mock_httphandler, ihandler = api_env
        rsp = client.get(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1"
        )
        assert rsp.status == "200 OK"

        json_rsp = rsp.get_json()
        suite_json = ihandler.report["MTest1"]["MT1Suite1"].shallow_serialize()
        assert json_rsp == suite_json

    def test_put(self, api_env):
        """Test updating the Suite resource via PUT."""
        client, mock_httphandler, ihandler = api_env

        suite_json = ihandler.report["MTest1"]["MT1Suite1"].shallow_serialize()
        suite_json["status"] = "running"
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1",
            json=suite_json,
        )
        assert rsp.status == "200 OK"
        assert rsp.get_json() == suite_json

        mock_httphandler.pool.apply_async.assert_called_once_with(
            ihandler.run_test_suite, ("MTest1", "MT1Suite1")
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, _, _ = api_env

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


class TestTestcases(object):
    """Test the Testcases resource."""

    def test_get(self, api_env):
        """Test reading the Testcases resource via GET."""
        client, mock_httphandler, ihandler = api_env
        rsp = client.get(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/testcases"
        )
        assert rsp.status == "200 OK"
        json_rsp = rsp.get_json()
        assert json_rsp == ["MT1S1TC1"]

    def test_put(self, api_env):
        """
        Test attempting to update the Testcases resource via PUT. This resource
        is read-only so PUT is not allowed.
        """
        client, _, _ = api_env
        rsp = client.put(
            "/api/v1/interactive/report/tests/MTest1/suites/MT1Suite1/testcases"
        )
        assert rsp.status == "405 METHOD NOT ALLOWED"


class TestTestcase(object):
    """Test the Testcase resource."""

    def test_get(self, api_env):
        """Test reading the Testcase resource via GET."""
        client, mock_httphandler, ihandler = api_env
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
        """Test updating the Testcase resource via PUT."""
        client, mock_httphandler, ihandler = api_env

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

        mock_httphandler.pool.apply_async.assert_called_once_with(
            ihandler.run_test_case, ("MTest1", "MT1Suite1", "MT1S1TC1")
        )

    def test_put_validation(self, api_env):
        """Test that 400 BAD REQUEST is returned for invalid PUT data."""
        client, _, _ = api_env

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
