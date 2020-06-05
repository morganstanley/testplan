import subprocess
import time
import sys
import os
import re
import threading
from six.moves import queue

import pytest
import requests

from testplan.common.utils.process import kill_process

_TIMEOUT = 60
_REQUEST_TIMEOUT = 0.5
_URL_RE = re.compile(r"^\s*Local: (?P<url>[^\s]+)\s*$")


@pytest.yield_fixture(
    scope="module",
    params=[
        ["dummy_programmatic_test_plan.py"],
        ["dummy_cli_arg_test_plan.py", "--ui"],
    ],
    ids=["webserver_exporter_programmatic", "webserver_exporter_cli_arg"],
)
def dummy_testplan(request):
    """
    Start the dummy testplan in a separate process. Terminate the dummy testplan
    and wait for the process to end.
    """
    cmd = [sys.executable] + request.param
    cwd = os.path.dirname(os.path.abspath(__file__))
    testplan_proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE)

    # Set up a thread to read from the process' stdout and write to a queue.
    # This prevents the main thread from blocking when there is no output.
    stdout_queue = queue.Queue()
    thr = threading.Thread(
        target=_enqueue_output, args=(testplan_proc.stdout, stdout_queue)
    )
    thr.daemon = True
    thr.start()

    yield testplan_proc, stdout_queue

    if testplan_proc.poll() is None:
        kill_process(testplan_proc)
    assert testplan_proc.poll() is not None

    thr.join(timeout=_TIMEOUT)
    assert not thr.is_alive()


def _enqueue_output(out, queue):
    """Enqueues lines from an output stream."""
    for line in iter(out.readline, b""):
        queue.put(line.decode("utf-8"))
    out.close()


def test_webserver_exporter(dummy_testplan):
    """
    WebServer Exporter should start a web server and respond to GET requests.
    Repeatedly send requests to the web server until it answers or timeout is
    hit.
    """
    # Unpack the process and stdout queue.
    proc, stdout_queue = dummy_testplan

    # By default Testplan will grab an ephemeral port to serve the UI, so we
    # must parse the stdout to find the URL.
    url = None
    timeout = time.time() + _TIMEOUT

    while (
        (url is None) and (proc.poll() is None) and ((time.time() < timeout))
    ):
        try:
            stdout_line = stdout_queue.get_nowait()
        except queue.Empty:
            time.sleep(0.1)
            continue
        print(stdout_line.rstrip("\n"))
        match = _URL_RE.match(stdout_line)
        if match:
            url = match.group("url")

    assert url is not None, "Failed to parse the webserver URL"

    # Now that we have the URL, try to make a GET request to it. This might
    # not immediately succeed so try a few times allowing for connection
    # errors. When the GET response is received, just verify the status code
    # is 200 OK.
    timeout = time.time() + _TIMEOUT
    status_code = None
    while time.time() < timeout:
        try:
            response = requests.get(url, timeout=_REQUEST_TIMEOUT)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ):
            time.sleep(_REQUEST_TIMEOUT)
        else:
            status_code = response.status_code
            break

    # Flush the stdout queue and print any remaining lines for debug.
    while not stdout_queue.empty():
        print(stdout_queue.get_nowait().rstrip("\n"))

    assert status_code == 200
