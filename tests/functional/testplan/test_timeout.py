import json
import os
import re
import psutil
import subprocess
import sys
import tempfile
import threading


def _timeout_cbk(proc):
    """
    Callback function called if the testplan subprocess doesn't terminate in a
    reasonable length of time.
    """
    proc.kill()
    raise RuntimeError('Timeout popped.')


def test_runner_timeout():
    """Test the globsl Testplan timeout feature."""
    testplan_script = os.path.join(
        os.path.dirname(__file__), 'test_plan_timeout.py')
    assert os.path.isfile(testplan_script)

    current_proc = psutil.Process()
    start_procs = current_proc.children()

    output_json = tempfile.NamedTemporaryFile(suffix='.json').name

    try:
        proc = subprocess.Popen(
            [sys.executable, testplan_script, '--json', output_json],
            stdout=subprocess.PIPE,
            universal_newlines=True)

        # Set our own timeout so that we don't wait forever if the testplan
        # script fails to timeout. 10 minutes ought to be long enough.
        # In Python 3 we could wait() with a timeout, but this is not
        # available in Python 2 so we need to roll our own timeout mechanism.
        timer = threading.Timer(300, _timeout_cbk, args=[proc])
        timer.start()
        stdout, _ = proc.communicate()
        timer.cancel()

        rc = proc.returncode

        with open(output_json, 'r') as json_file:
            report = json.load(json_file)

        # Check that the testplan exited with an error status.
        assert rc == 1
        assert report['status'] == 'error'

        # Check that the timeout is logged to stdout.
        if not re.search(r'Timeout: Aborting execution after 5 seconds',
                         stdout):
            print(stdout)
            raise RuntimeError('Timeout log not found in stdout')

        # Check that no extra child processes remain since before starting.
        assert current_proc.children() == start_procs
    finally:
        os.remove(output_json)
        pass
