import subprocess
import time
import sys
import os

import pytest
import requests

from testplan.common.utils.process import kill_process
from testplan import defaults

TIMEOUT = 60
REQUEST_TIMEOUT = 0.1

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
    testplan_proc = subprocess.Popen(cmd, cwd=cwd)
    yield testplan_proc
    kill_process(testplan_proc)

def test_webserver_exporter(dummy_testplan):
    """
    WebServer Exporter should start a web server and respond to GET requests.
    Repeatedly send requests to the web server until it answers or timeout is
    hit.
    """
    url = 'http://{host}:{port}/testplan/local'.format(
        host=defaults.WEB_SERVER_HOSTNAME,
        port=defaults.WEB_SERVER_PORT
    )
    timeout = time.time() + TIMEOUT
    status_code = None
    while time.time() < timeout:
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout):
            time.sleep(REQUEST_TIMEOUT)
        else:
            status_code = response.status_code
            break
    assert status_code == 200
