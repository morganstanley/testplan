import os
import re
import runpy
import sys
from traceback import format_exc

import pytest

from testplan.common.utils.path import change_directory


SUCCES_EXIT_CODES = (
    0,
    False,
    None,
)  # these considered as 0 return value and means success


def run_example_in_process(filename, root, known_exceptions, cmdline_args=[]):
    file_path = os.path.join(root, filename)
    try:

        # set up like an external invocation.
        # add current dir to fron of sys path
        # no arguments pass in command line

        sys.path.insert(0, root)
        argv = sys.argv
        sys.argv = [sys.argv[0], *cmdline_args]

        with change_directory(root), open(filename) as file_obj:
            file_obj.readline()
            second_line = file_obj.readline()

            runpy.run_path(os.path.join(root, filename), run_name="__main__")

    except SystemExit as e:
        if e.code not in SUCCES_EXIT_CODES:
            assert (
                "# This plan contains tests that demonstrate failures as well."
            ) == second_line.strip(), (
                "Expected '{}' example to pass, it failed".format(file_path)
            )
    except Exception as e:
        for exception in known_exceptions:
            if re.search(exception, "{}: {}".format(type(e).__name__, str(e))):
                pytest.xfail()
        pytest.fail(format_exc())
    finally:
        # clean up after execution
        # remove the modules imported from the directory of testplan_path
        # remove the added toot from sys.path
        # reset the args as it was before execution

        for m in get_local_modules(root):
            del sys.modules[m]

        sys.path = sys.path[1:]
        sys.argv = argv


def get_local_modules(path_prefix):
    """
    return module names loaded from a path with path_prefix

    :param path_prefix:
    :return:
    """
    return set(
        n
        for n, m in sys.modules.items()
        if hasattr(m, "__file__")
        and m.__file__
        and m.__file__.startswith(path_prefix)
    )
