import json
import os
import re
import psutil
import subprocess
import sys
import tempfile


def test_runner_timeout():
    """Test the globsl Testplan timeout feature."""
    testplan_script = os.path.join(
        os.path.dirname(__file__), "timeout_test_plan.py"
    )
    assert os.path.isfile(testplan_script)

    current_proc = psutil.Process()
    start_procs = current_proc.children()

    output_json = tempfile.NamedTemporaryFile(suffix=".json").name

    try:
        proc = subprocess.Popen(
            [sys.executable, testplan_script, "--json", output_json],
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )

        # Set our own timeout so that we don't wait forever if the testplan
        # script fails to timeout. 5 minutes ought to be long enough.
        try:
            proc.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()

        rc = proc.returncode

        with open(output_json, "r") as json_file:
            report = json.load(json_file)

        # Check that the testplan exited with an error status.
        assert rc == 1
        assert len(report["entries"]) == 2
        assert report["status"] == "error"
        assert report["counter"]["error"] == 1

        # Check that the timeout is logged to stdout.
        if not re.search(
            r"Timeout: Aborting execution after 5 seconds",
            report["logs"][0]["message"],
        ):
            raise RuntimeError("Timeout log not found")

        # Check that no extra child processes remain since before starting.
        assert current_proc.children() == start_procs
    finally:
        os.remove(output_json)
