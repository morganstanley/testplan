"""All default values that will be shared between config objects go here."""

import os

from testplan.report.testing.styles import StyleArg

TESTPLAN_TIMEOUT = 14400  # 4h

SUMMARY_NUM_PASSING = 5
SUMMARY_NUM_FAILING = 5
SUMMARY_KEY_COMB_LIMIT = 10  # Number of failed key combinations to summary.

# Make sure these values match the defaults in the parser.py,
# otherwise we may end up with inconsistent behaviour re. defaults
# between cmdline and programmatic calls.
PDF_STYLE = StyleArg.SUMMARY.value
STDOUT_STYLE = StyleArg.EXTENDED_SUMMARY.value

REPORT_DIR = os.getcwd()
XML_DIR = os.path.join(REPORT_DIR, "xml")
PDF_PATH = os.path.join(REPORT_DIR, "report.pdf")
JSON_PATH = os.path.join(REPORT_DIR, "report.json")
ATTACHMENTS = "_attachments"
RESOURCE_DATA = "_resource"
RESOURCE_META_FILE_NAME = "metadata.json"
ATTACHMENTS_DIR = os.path.join(REPORT_DIR, ATTACHMENTS)
RESOURCE_DATA_DIR = os.path.join(REPORT_DIR, RESOURCE_DATA)

WEB_SERVER_HOSTNAME = "0.0.0.0"
WEB_SERVER_PORT = 0
WEB_SERVER_TIMEOUT = 10

# Default to using 4 threads for interactive pool.
INTERACTIVE_POOL_SIZE = 4

# Name of multitest/testsuite/testcase (usually used for display) cannot be
# too long, or the UI will not be pleasant when they end up with long names
MAX_TEST_NAME_LENGTH = 255

# Default to using 30 min for auto-parts task.
AUTO_PART_RUNTIME_MAX = 30 * 60
# Each part shall be at least 8 min
AUTO_PART_RUNTIME_MIN = 8 * 60
# Expect to finish within 3 times of the longest start+stop time
START_STOP_FACTOR = 3

# Default to using 30min for calculating pool size
PLAN_RUNTIME_TARGET = 1800  # 30 min
