import subprocess
import time
import sys
import os
import re
import threading

import pytest
import requests

from testplan.common.utils.process import kill_process
from testplan import defaults

_TIMEOUT = 60
_REQUEST_TIMEOUT = 0.1
_URL_RE = re.compile(
    r'^View the JSON report in the browser: (?P<url>[^\s]+)\s*$')


@pytest.yield_fixture(
    scope='module',
    params=[
        ['dummy_programmatic_test_plan.py'],
        ['dummy_cli_arg_test_plan.py', '--ui']
    ],
    ids=['webserver_exporter_programmatic', 'webserver_exporter_cli_arg']
)
def dummy_testplan(request):
    """
    Start the dummy testplan in a separate process. Terminate the dummy testplan
    and wait for the process to end.
    """
    cmd = [sys.executable] + request.param
    cwd = os.path.dirname(os.path.abspath(__file__))
    testplan_proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE)

    yield testplan_proc

    if testplan_proc.poll() is None:
        kill_process(testplan_proc)
    assert testplan_proc.poll() is not None

def test_webserver_exporter(dummy_testplan):
    """
    WebServer Exporter should start a web server and respond to GET requests.
    Repeatedly send requests to the web server until it answers or timeout is
    hit.
    """
    # By default Testplan will grab an ephemeral port to serve the UI, so we
    # must parse the stdout to find the URL.
    url = None

    while (url is None) and (dummy_testplan.poll() is None):
        stdout_line = dummy_testplan.stdout.readline().decode('ascii')
        match = _URL_RE.match(stdout_line)
        if match:
            url = match.group('url')

    assert url is not None, 'Failed to parse the webserver URL'

    # Now that we have the URL, try to make a GET request to it. This might
    # not immediately succeed so try a few times allowing for connection
    # errors. When the GET response is received, just verify the status code
    # is 200 OK.
    timeout = time.time() + _TIMEOUT
    status_code = None
    while time.time() < timeout:
        try:
            response = requests.get(url, timeout=_REQUEST_TIMEOUT)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout):
            time.sleep(_REQUEST_TIMEOUT)
        else:
            status_code = response.status_code
            break
    assert status_code == 200

