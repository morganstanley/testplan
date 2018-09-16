#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
Parallel test execution in a remote pool.
"""

import os
import sys
import socket
import getpass

from testplan import test_plan, Task
from testplan.runners.pools import RemotePool

from testplan.common.utils.path import module_abspath, pwd

from testplan.parser import TestplanParser
from testplan.report.testing.styles import Style, StyleEnum

OUTPUT_STYLE = Style(StyleEnum.ASSERTION_DETAIL, StyleEnum.ASSERTION_DETAIL)


class CustomParser(TestplanParser):
    """Inheriting base parser."""

    def add_arguments(self, parser):
        """Defining custom arguments for this Testplan."""
        parser.add_argument('--tasks-num',
                            action='store', type=int, default=8)
        parser.add_argument('--pool-size',
                            action='store', type=int, default=4)


# Function that creates a file with some content
# to demonstrate custom file transferring.
def make_file(filename, content):
    temp_dir = os.path.join(os.sep, 'var', 'tmp', getpass.getuser())
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    path = os.path.join(temp_dir, filename)
    with open(path, 'w') as fobj:
        fobj.write(content)
    return path


def linux_paths(paths):
    # In case of windows local host.
    return ['/'.join(path.split(os.sep)) for path in paths]


# Using a custom parser to support `--tasks-num` and `--pool-size` command
# line arguments so that users can experiment with remote pool test execution.

# Hard-coding `pdf_path`, 'stdout_style' and 'pdf_style' so that the
# downloadable example gives meaningful and presentable output.
# NOTE: this programmatic arguments passing approach will cause Testplan
# to ignore any command line arguments related to that functionality.
@test_plan(name='RemotePoolExecution',
           parser=CustomParser,
           pdf_path=os.path.join(pwd(), 'report.pdf'),
           stdout_style=OUTPUT_STYLE,
           pdf_style=OUTPUT_STYLE)
def main(plan):
    """
    Testplan decorated main function to add and execute MultiTests.

    :return: Testplan result object.
    :rtype:  ``testplan.base.TestplanResult``
    """
    import testplan
    workspace = os.path.abspath(
        os.path.join(
            os.path.dirname(module_abspath(testplan)),
            '..', '..'))

    # Static local file examples.
    source_files = [make_file('file1', 'File1'), make_file('file2', 'File2')]

    # Add a remote pool test execution resource to the plan of given size.
    pool = RemotePool(name='MyPool',
                      hosts={socket.gethostname(): 3},
                      setup_script=['/bin/bash', 'setup_script.ksh'],
                      env={'LOCAL_USER': getpass.getuser(),
                           'LOCAL_WORKSPACE': workspace},
                      workspace_exclude=['.git/', '.cache/', 'doc/', 'test/'],
                      push=source_files,
                      workspace=workspace)

    plan.add_resource(pool)

    # Add a given number of similar tests to the remote pool
    # to be executed in parallel.
    for idx in range(plan.args.tasks_num):
        # All Task arguments need to be serializable.
        task = Task(target='make_multitest',
                    module='tasks',
                    path='.',
                    kwargs={'index': idx,
                            'files': linux_paths(source_files)})
        plan.schedule(task, resource='MyPool')


if __name__ == '__main__':
    res = main()
    print('Exiting code: {}'.format(res.exit_code))
    sys.exit(res.exit_code)
