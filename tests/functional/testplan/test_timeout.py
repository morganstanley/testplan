import json
import os
import re
import psutil
import subprocess
import sys
import tempfile
import time
import threading


def timeout_cbk(proc):
    proc.kill()
    raise RuntimeError('Timeout popped.')


def test_runner_timeout():
    """Test the globsl Testplan timeout feature."""
    testplan_script = os.path.join(
        os.path.dirname(__file__), 'test_plan_timeout.py')
    assert os.path.isfile(testplan_script)

    current_proc = psutil.Process()
    start_procs = current_proc.children()

    with tempfile.NamedTemporaryFile(mode='r') as output_json:
        proc = subprocess.Popen(
            [sys.executable, testplan_script, '--json', output_json.name],
            stdout=subprocess.PIPE)

        # Set our own timeout so that we don't wait forever if the testplan
        # script fails to timeout. 10 minutes ought to be long enough.
        # In Python 3 we could wait() with a timeout, but this is not
        # available in Python 2 so we need to roll our own timeout mechanism.
        timer = threading.Timer(300, timeout_cbk, args=[proc])
        timer.start()
        stdout_bytes, _ = proc.communicate()
        timer.cancel()

        stdout = stdout_bytes.decode('utf-8')
        rc = proc.returncode

        report = json.load(output_json)

    # Check that the testplan exited with an error status.
    assert rc == 1
    assert report['status'] == 'error'

    # Check that the timeout is logged to stdout.
    assert re.match(r'^Timeout: Aborting execution after 5 seconds$',
                    stdout,
                    flags=re.MULTILINE)

    # Check that no extra child processes remain since before starting.
    assert current_proc.children() == start_procs
