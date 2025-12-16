"""
Enum for different trace levels in Testplan.
This needs to be in a separate file to prevent pickling of the tracing object
"""

from enum import IntEnum


class TraceLevel(IntEnum):
    NONE = 0
    PLAN = 1
    TEST = 2
    TESTSUITE = 3
    TESTCASE = 4

    def __str__(self):
        return self.name.capitalize()
