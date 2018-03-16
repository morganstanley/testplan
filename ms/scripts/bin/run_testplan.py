"""
from: .../testplan/examples/MyApp/Converter
python ../../../../ms/scripts/bin/run_testplan.py ./test_plan.py
"""

import os
import sys
import signal
import subprocess

signal.signal(signal.SIGINT, signal.SIG_IGN)

os.environ['PYTHONPATH'] = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', '..', '..')
os.environ['TESTPLAN_DEPENDENCIES_PATH'] = os.path.dirname(
    os.path.abspath(__file__))

cmd = ' '.join([sys.executable] + sys.argv[1:])
print('Running: {}'.format(cmd))
sys.exit(subprocess.call(cmd, shell=True))
