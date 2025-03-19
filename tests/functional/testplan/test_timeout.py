import json
import os
import re
import subprocess
import sys
import tempfile

import psutil


def test_runner_timeout():
    """
    Tests the global Testplan timeout feature.
    """
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
        # Check that the report contains 2 MultiTest + 1 Timeout entries
        assert len(report["entries"]) == 3
        assert report["entries"][2]["name"] == "Testplan timeout"
        # Check that the timed out MultiTest is marked as incomplete.
        assert report["entries"][1]["status"] == "incomplete"
        assert report["status"] == "error"
        # Check that the timeout is logged to stdout.
        if not re.search(
            r"Timeout: Aborting execution after 10 seconds",
            report["logs"][0]["message"],
        ):
            raise RuntimeError("Timeout information not found in log")

        # Check that no extra child processes remain since before starting.
        assert current_proc.children() == start_procs

    finally:
        os.remove(output_json)
