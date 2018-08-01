"""Module containing Testplan main class."""

import os
import sys

sys.dont_write_bytecode = True

TESTPLAN_DEPENDENCIES_PATH = 'TESTPLAN_DEPENDENCIES_PATH'
if TESTPLAN_DEPENDENCIES_PATH in os.environ:
    print('Importing testplan dependencies from: {}'.format(
        os.environ[TESTPLAN_DEPENDENCIES_PATH]))
    sys.path.insert(0, os.environ[TESTPLAN_DEPENDENCIES_PATH])
    import dependencies
    sys.path.pop(0)

from .base import Testplan, TestplanConfig, TestplanResult, test_plan
from .runners.pools.tasks import Task, TaskResult
