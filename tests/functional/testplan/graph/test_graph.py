import json
import os
import re
import psutil
import subprocess
import sys
import tempfile


def test_graph():
    """Test the globsl Testplan timeout feature."""
    testplan_script = os.path.join(
        os.path.dirname(__file__), 'test_plan_graph.py')
    assert os.path.isfile(testplan_script)

    cuurent_path = os.path.dirname(os.path.realpath(__file__))
    output_json = tempfile.NamedTemporaryFile(suffix='.json', dir=cuurent_path).name

    try:
        proc = subprocess.Popen(
            [sys.executable, testplan_script, '--json', output_json],
            stdout=subprocess.PIPE,
            universal_newlines=True)

        stdout, _ = proc.communicate()
        rc = proc.returncode

        with open(output_json, 'r') as json_file:
            report = json.load(json_file)

        # Check that the valid testplan exited with an passed status.
        assert rc == 0
        assert report['status'] == 'passed'

        # Check that the JSON outputted contains the correct components.
        testcase1 = report['entries'][0]['entries'][0]['entries'][0]['entries'][0]
        assert testcase1['type'] == 'Graph'
        assert testcase1['graph_type'] == 'Line'
        assert testcase1['graph_data'] == [{'x': 1, 'y': 2}, {'x': 3, 'y': 4}]
        assert testcase1['description'] == 'Desciptions :]'
        assert testcase1['options'] == {'colour': 'red'}

        testcase2 = report['entries'][0]['entries'][0]['entries'][0]['entries'][1]
        assert testcase2['options'] is None

        testcase3 = report['entries'][0]['entries'][0]['entries'][0]['entries'][2]
        assert testcase3['description'] is None
        assert testcase3['options'] is None

    finally:
        os.remove(output_json)
