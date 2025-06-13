#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
Parallel test execution in a remote pool.
"""

import os
import sys
import getpass
import shutil
import tempfile

# Check if the remote host has been specified in the environment. Remote
# hosts can only be Linux systems.
REMOTE_HOST = os.environ.get("TESTPLAN_REMOTE_HOST")
if not REMOTE_HOST:
    raise RuntimeError(
        "You must specify a remote Linux host via the TESTPLAN_REMOTE_HOST "
        "environment var to run this example."
    )

from testplan import test_plan
from testplan import Task
from testplan.runners.pools.remote import RemotePool

from testplan.common.utils.path import pwd

from testplan.parser import TestplanParser
from testplan.report.testing.styles import Style, StyleEnum

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)
TEMP_DIR = None


class CustomParser(TestplanParser):
    """Inheriting base parser."""

    def add_arguments(self, parser):
        """Defining custom arguments for this Testplan."""
        parser.add_argument("--tasks-num", action="store", type=int, default=8)
        parser.add_argument("--pool-size", action="store", type=int, default=4)


# Function that creates a file with some content
# to demonstrate custom file transferring.
def make_file(filename, dirname, content):
    path = os.path.join(dirname, filename)
    with open(path, "w") as fobj:
        fobj.write(content)
    return path


# Using a custom parser to support `--tasks-num` and `--pool-size` command
# line arguments so that users can experiment with remote pool test execution.


# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(
    name="RemotePoolExecution",
    parser=CustomParser,
    pdf_path=os.path.join(pwd(), "report.pdf"),
    stdout_style=OUTPUT_STYLE,
    pdf_style=OUTPUT_STYLE,
)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """

    workspace = os.path.dirname(__file__)

    # Create two temporary files locally. For demonstration, just write the
    # filename as the content of each.
    assert TEMP_DIR is not None
    for filename in ("file1", "file2"):
        make_file(filename, TEMP_DIR, content=filename)

    # Explicitly specify the full paths to both the local source files just
    # created and the destination filepaths on the remote host.
    push_files = [
        (os.path.join(TEMP_DIR, "file1"), "/tmp/remote_example/file1"),
        (os.path.join(TEMP_DIR, "file2"), "/tmp/remote_example/file2"),
    ]

    # Add a remote pool test execution resource to the plan of given size.
    pool = RemotePool(
        name="MyPool",
        # Create 3 workers on the same remote host.
        hosts={REMOTE_HOST: 3},
        # Allow the remote port to be overridden by the
        # environment. Default to 0, which will make testplan use
        # the default SSH port for connections.
        port=int(os.environ.get("TESTPLAN_REMOTE_PORT", 0)),
        setup_script=["/bin/bash", "setup_script.ksh"],
        env={"LOCAL_USER": getpass.getuser(), "LOCAL_WORKSPACE": workspace},
        workspace_exclude=[".git/", ".cache/", "doc/", "test/"],
        # We push local files to the remote worker using the
        # explicit source and destination locations defined above.
        push=push_files,
        workspace=workspace,
        clean_remote=True,
    )

    plan.add_resource(pool)

    # Add a given number of similar tests to the remote pool
    # to be executed in parallel.
    for idx in range(plan.args.tasks_num):
        # All Task arguments need to be serializable.
        task = Task(
            target="make_multitest",
            module="tasks",
            # We specify the full paths to files as they will be found
            # on the remote host.
            kwargs={
                "index": idx,
                "files": [
                    "/tmp/remote_example/file1",
                    "/tmp/remote_example/file2",
                ],
            },
        )
        plan.schedule(task, resource="MyPool")


if __name__ == "__main__":
    # Create a new temporary directory for this test plan.
    TEMP_DIR = tempfile.mkdtemp()

    # Run the test plan.
    res = main()

    # Clean up all the temporary files used by this test plan.
    shutil.rmtree(TEMP_DIR)

    print("Exiting code: {}".format(res.exit_code))
    sys.exit(res.exit_code)
