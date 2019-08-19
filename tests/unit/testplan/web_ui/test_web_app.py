import os
import uuid
import shutil
import tempfile

import pytest

from testplan import defaults
from testplan.web_ui.web_app import app as tp_web_app

STATIC_REPORTS = {
    'testing': {
        'uid': str(uuid.uuid4()),
        'contents': str(uuid.uuid4()),
    },
}

DATA_REPORTS = {
    'testplan': {
        'report_name': 'report.json',
        'uid': str(uuid.uuid4()),
        'contents': str(uuid.uuid4()),
    },
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

    with open(tmp_file, 'w') as tmp_file:
        tmp_file.write(str(contents))


def _create_tmp_static_files(base_dir):
    """
    Create fake static files to be sent by the Testplan web app.
        <STATIC_PATH>/testplan/build/index.html
        <STATIC_PATH>/testplan/build/static.file

    :param base_dir: The Testplan web app's STATIC_PATH directory.
    :type base_dir: ``str``
    """
    for report_type, report in list(STATIC_REPORTS.items()):
        index_file = os.path.join(base_dir, report_type, 'build', 'index.html')
        _create_tmp_file(tmp_file=index_file, contents=report['contents'])
        static_file = os.path.join(
            base_dir, report_type, 'build', 'static', 'static.file')
        _create_tmp_file(tmp_file=static_file, contents=report['contents'])


def _create_tmp_data_files(base_dir):
    """
    Create fake data files to be sent by the Testplan web app.
        <DATA_PATH>/reports/testplan_<UID>/report.json
        <DATA_PATH>/reports/monitor_<UID>/report.json

    :param base_dir: The Testplan web app's DATA_PATH directory.
    :type base_dir: ``str``
    """
    for report_type, report in list(DATA_REPORTS.items()):
        report_file = os.path.join(base_dir, report['report_name'])
        _create_tmp_file(tmp_file=report_file, contents=report['contents'])
    attachment_file = os.path.join(base_dir, defaults.ATTACHMENTS, 'attached.file')
    _create_tmp_file(tmp_file=attachment_file, contents=DATA_REPORTS['testplan']['contents'])


class TestStaticEndpoints(object):
    """
    Test the endpoints returning files from the STATIC_PATH directory.
    """

    def setup_method(self, _):
        """Create fake static files and a test client."""
        self.static_dir = tempfile.mkdtemp()
        _create_tmp_static_files(self.static_dir)
        tp_web_app.config['STATIC_PATH'] = self.static_dir
        tp_web_app.config['TESTPLAN_REPORT_NAME'] = 'report.json'
        tp_web_app.config['TESTING'] = True
        tp_web_app.static_folder = os.path.abspath(
            os.path.join(
                tp_web_app.config['STATIC_PATH'], 'testing', 'build', 'static'
            )
        )
        self.app = tp_web_app
        self.client = tp_web_app.test_client()

    def teardown_method(self, _):
        """Remove fake static files."""
        shutil.rmtree(self.static_dir)

    def test_testplan_index(self):
        """Does /testplan/<uid> return the correct index.html page."""
        # Use correct UID, expect 200 response.
        response = self.client.get('/testplan/{}'.format(
            STATIC_REPORTS['testing']['uid']))
        expected_contents = str(STATIC_REPORTS['testing']['contents'])
        assert response.status_code == 200
        assert expected_contents in str(response.data)

        # Use incorrect UID, still expect 200 response.
        response = self.client.get('/testplan/123')
        assert response.status_code == 200
        assert expected_contents in str(response.data)

    def test_testplan_static(self):
        """
        Does /testplan/static/static.file respond with the static.file file.
        """
        # Use correct UID, expect 200 response
        response = self.client.get('/static/static.file')
        expected_contents = str(STATIC_REPORTS['testing']['contents'])
        assert response.status_code == 200
        assert expected_contents in str(response.data)

        # This endpoint should return the index.html page no matter what UID is
        # sent
        response = self.client.get('/testplan/static/123')
        assert response.status_code == 404
        assert expected_contents not in str(response.data)


class TestDataEndpoints(object):
    """
    Test the endpoints returning files from the DATA_PATH directory.
    """

    def setup_method(self, _):
        """Create fake data files and a test client."""
        self.data_dir = tempfile.mkdtemp()
        _create_tmp_data_files(self.data_dir)
        tp_web_app.config['DATA_PATH'] = self.data_dir
        tp_web_app.config['TESTING'] = True
        self.client = tp_web_app.test_client()

    def teardown_method(self, _):
        """Remove fake data files."""
        shutil.rmtree(self.data_dir)

    def test_testplan_report(self):
        """Does /api/v1/reports/<uid>/report return the correct report.json file."""
        # Use correct UID, expect 200 response.
        path = '/api/v1/reports/{}'.format(DATA_REPORTS['testplan']['uid'])
        response = self.client.get(path)
        expected_contents = str(DATA_REPORTS['testplan']['contents'])
        assert response.status_code == 200
        assert expected_contents in str(response.data)

        # Use incorrect UID, still expect 200 response.
        response = self.client.get('/api/v1/reports/123')
        assert response.status_code == 200
        assert expected_contents in str(response.data)

    def test_testplan_assertions(self):
        """
        Does sending anything to /api/v1/reports/<uid>/assertions/<uid> respond with
        501.
        """
        response = self.client.get('api/v1/reports/123/assertions/123')
        assert response.status_code == 501

    def test_testplan_attachment(self):
        """
        Does sending anything to /api/v1/reports/<uid>/attachments/<uid> respond with
        501.
        """
        path = '/api/v1/reports/123/attachments/attached.file'
        response = self.client.get(path)
        expected_contents = str(DATA_REPORTS['testplan']['contents'])
        assert response.status_code == 200
        assert expected_contents in str(response.data)

