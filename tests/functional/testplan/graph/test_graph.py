import json
import os
import subprocess
import sys
import tempfile


def test_graph():
    """Test the graphing feature."""
    testplan_script = os.path.join(
        os.path.dirname(__file__), 'graph_example.py')
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
        assert type(testcase1['graph_data']) is dict
        assert testcase1['description'] == 'Line Graph'
        assert type(testcase1['series_options']) is dict
        assert testcase1['graph_options'] is None

        testcase2 = report['entries'][0]['entries'][0]['entries'][0]['entries'][1]
        assert testcase2['graph_type'] == 'Bar'
        assert testcase2['series_options'] is None
        assert testcase2['graph_options'] is None

        testcase3 = report['entries'][0]['entries'][0]['entries'][0]['entries'][2]
        assert testcase3['type'] == 'DiscreteChart'
        assert type(testcase3['series_options']) is dict
        assert testcase3['graph_options'] is None

        testcase4 = report['entries'][0]['entries'][0]['entries'][0]['entries'][3]
        assert type(testcase4['graph_data']) is dict
        assert len(testcase4['graph_data']) is 2

    finally:
        os.remove(output_json)
