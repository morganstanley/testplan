import os
import uuid
import shutil
import tempfile

import pytest

from testplan import defaults
from testplan.web_ui.web_app import app as tp_web_app

STATIC_REPORTS = {
    "testing": {"uid": "static-uid", "contents": "Static content"}
}

DATA_REPORTS = {
    "testplan": {
        "report_name": "report.json",
        "uid": "test-report-uid",
        "contents": "This is a JSON report",
    }
}


def _create_tmp_file(tmp_file, contents):
    """
    Create the given file, and it's base directory if necessary.
    Fill the file with the given contents.

    :param tmp_file: Name of the file to be created (including path).
    :type tmp_file: ``str``
    :param contents: Contents of the file to be created.
    :type contents: ``str``
    """
    base_dir = os.path.dirname(tmp_file)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    with open(tmp_file, "w") as tmp_file:
        tmp_file.write(contents)


def _create_tmp_static_files(base_dir):
    """
    Create fake static files to be sent by the Testplan web app.
        <STATIC_PATH>/testplan/build/index.html
        <STATIC_PATH>/testplan/build/static.file

    :param base_dir: The Testplan web app's STATIC_PATH directory.
    :type base_dir: ``str``
    """
    for report_type, report in list(STATIC_REPORTS.items()):
        index_file = os.path.join(base_dir, report_type, "build", "index.html")
        _create_tmp_file(tmp_file=index_file, contents=report["contents"])
        static_file = os.path.join(
            base_dir, report_type, "build", "static", "static.file"
        )
        _create_tmp_file(tmp_file=static_file, contents=report["contents"])


def _create_tmp_data_files(base_dir):
    """
    Create fake data files to be sent by the Testplan web app.
        <DATA_PATH>/reports/testplan_<UID>/report.json
        <DATA_PATH>/reports/monitor_<UID>/report.json

    :param base_dir: The Testplan web app's DATA_PATH directory.
    :type base_dir: ``str``
    """
    for report_type, report in list(DATA_REPORTS.items()):
        report_file = os.path.join(base_dir, report["report_name"])
        _create_tmp_file(tmp_file=report_file, contents=report["contents"])
    attachment_file = os.path.join(
        base_dir, defaults.ATTACHMENTS, "attached.file"
    )
    _create_tmp_file(
        tmp_file=attachment_file, contents=DATA_REPORTS["testplan"]["contents"]
    )


@pytest.fixture
def webapp_test_client():
    """Create fake data files and a test client."""
    data_dir = tempfile.mkdtemp()
    static_dir = tempfile.mkdtemp()
    _create_tmp_data_files(data_dir)
    _create_tmp_static_files(static_dir)
    tp_web_app.config["STATIC_PATH"] = static_dir
    tp_web_app.config["DATA_PATH"] = data_dir
    tp_web_app.config["TESTPLAN_REPORT_NAME"] = "report.json"
    tp_web_app.config["TESTING"] = True
    tp_web_app.static_folder = os.path.abspath(
        os.path.join(
            tp_web_app.config["STATIC_PATH"], "testing", "build", "static"
        )
    )
    client = tp_web_app.test_client()
    yield client
    shutil.rmtree(data_dir)
    shutil.rmtree(static_dir)


def test_testplan_index(webapp_test_client):
    """Does /testplan/<uid> return the correct index.html page."""
    # Use correct UID, expect 200 response.
    response = webapp_test_client.get(
        "/testplan/{}".format(STATIC_REPORTS["testing"]["uid"])
    )
    expected_contents = str(STATIC_REPORTS["testing"]["contents"])
    assert response.status_code == 200
    assert expected_contents in str(response.data)

    # Use incorrect UID, still expect 200 response.
    response = webapp_test_client.get("/testplan/123")
    assert response.status_code == 200
    assert expected_contents in str(response.data)


def test_testplan_static(webapp_test_client):
    """
    Does /testplan/static/static.file respond with the static.file file.
    """
    # Use correct UID, expect 200 response
    response = webapp_test_client.get("/static/static.file")
    expected_contents = str(STATIC_REPORTS["testing"]["contents"])
    assert response.status_code == 200
    assert expected_contents in str(response.data)

    # This endpoint should return the index.html page no matter what UID is
    # sent
    response = webapp_test_client.get("/testplan/static/123")
    assert response.status_code == 200
    assert expected_contents in str(response.data)


def test_testplan_report(webapp_test_client):
    """Does /api/v1/reports/<uid>/report return the correct report.json file."""
    # Use correct UID, expect 200 response.
    path = "/api/v1/reports/{}".format(DATA_REPORTS["testplan"]["uid"])
    response = webapp_test_client.get(path)
    expected_contents = str(DATA_REPORTS["testplan"]["contents"])
    assert response.status_code == 200
    assert expected_contents in str(response.data)

    # Use incorrect UID, still expect 200 response.
    response = webapp_test_client.get("/api/v1/reports/123")
    assert response.status_code == 200
    assert expected_contents in str(response.data)


def test_testplan_assertions(webapp_test_client):
    """
    Does sending anything to /api/v1/reports/<uid>/assertions/<uid> respond with
    501.
    """
    response = webapp_test_client.get("api/v1/reports/123/assertions/123")
    assert response.status_code == 501


def test_testplan_attachment(webapp_test_client):

    path = "/api/v1/reports/123/attachments/attached.file"
    response = webapp_test_client.get(path)
    expected_contents = str(DATA_REPORTS["testplan"]["contents"])
    assert response.status_code == 200
    assert expected_contents in str(response.data)


def test_testplan_fix_spec(webapp_test_client):
    """Does /api/v1/metadata/fix-spec/tags return the correct dictionary."""
    # Expect information of all tags
    path = "/api/v1/metadata/fix-spec/tags"
    response = webapp_test_client.get(path)
    assert response.status_code == 200
    tags_info = response.json
    assert isinstance(tags_info, dict)
    assert tags_info["8"]["names"][0] == "BeginString"
    assert tags_info["9"]["names"][0] == "BodyLength"
    assert tags_info["10"]["names"][0] == "CheckSum"

    # Use valid tag number and get the enumeration information
    tag = 40
    path = f"/api/v1/metadata/fix-spec/tags/{tag}/enum-vals"
    response = webapp_test_client.get(path)
    assert response.status_code == 200
    enum_info = response.json
    assert isinstance(enum_info, list)
    assert len(enum_info) > 0
    assert set(enum_info[0].keys()) == {"value", "descr"}

    # Use invalid tag number still 200 response but no data.
    tag = 10
    path = f"/api/v1/metadata/fix-spec/tags/{tag}/enum-vals"
    response = webapp_test_client.get(path)
    assert response.status_code == 200
    enum_info = response.json
    assert isinstance(enum_info, list)
    assert len(enum_info) == 0
