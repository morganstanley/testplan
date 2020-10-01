"""All default values that will be shared between config objects go here."""
import os
import math

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
ATTACHMENTS_DIR = os.path.join(REPORT_DIR, ATTACHMENTS)

WEB_SERVER_HOSTNAME = "0.0.0.0"
WEB_SERVER_PORT = 0
WEB_SERVER_TIMEOUT = 10

# Default to using 4 threads for interactive pool.
INTERACTIVE_POOL_SIZE = 4

# Name of multitest/testsuite/testcase (usually used for display) cannot be
# too long, or the UI will not be pleasant when they end up with long names
MAX_MULTITEST_NAME_LENGTH = math.inf  # 120
MAX_TESTSUITE_NAME_LENGTH = math.inf  # 120
MAX_TESTCASE_NAME_LENGTH = math.inf  # 120
