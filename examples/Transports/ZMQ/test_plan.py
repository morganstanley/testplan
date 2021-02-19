#!/usr/bin/env python
"""
Testplan to run all ZMQ examples.
"""

import sys

from testplan import test_plan
from testplan.report.testing.styles import Style, StyleEnum
import zmq_pair_connection
import zmq_publish_subscribe_connection

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


@test_plan(
    name="ZMQConnections",
    pdf_path="report.pdf",
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
)
def main(plan):
    plan.add(zmq_pair_connection.get_multitest("ZMQPAIRConnection"))
    plan.add(
        zmq_publish_subscribe_connection.get_multitest("ZMQPUBSUBConnection")
    )


if __name__ == "__main__":
    res = main()
    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
