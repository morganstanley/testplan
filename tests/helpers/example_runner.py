import sys
import os
import re
import runpy
import copy
import traceback

import pytest

from testplan.common.utils.path import change_directory


SUCCES_EXIT_CODES = (
    0,
    False,
    None,
)  # these considered as 0 return value and means success


def run_example_in_process(
    filename, root, known_exceptions, cmdline_args=None
):
    sys_path = copy.copy(sys.path)
    sys_argv = copy.copy(sys.argv)

    cmdline_args = cmdline_args or []
    file_path = os.path.join(root, filename)
    second_line = ""

    try:
        # set up like an external invocation.
        # add current dir to front of sys.path
        # no arguments pass in command line

        sys.path.insert(0, root)
        sys.argv = [""] + cmdline_args

        with change_directory(root), open(filename) as file_obj:
            file_obj.readline()
            second_line = file_obj.readline().strip()
            runpy.run_path(os.path.join(root, filename), run_name="__main__")

    except SystemExit as e:
        if e.code not in SUCCES_EXIT_CODES:
            assert (
                "# This plan contains tests that demonstrate failures as well."
            ) == second_line, (
                'Expected "{}" example to pass, it failed'.format(file_path)
            )
    except Exception as e:
        for exception in known_exceptions:
            if re.search(exception, "{}: {}".format(type(e).__name__, str(e))):
                pytest.xfail()
        pytest.fail(traceback.format_exc())
    finally:
        # clean up after execution
        # remove the modules imported from the directory of testplan_path
        # remove the added root from sys.path
        # reset the args as it was before execution

        for mod_name in get_local_modules(root):
            del sys.modules[mod_name]

        sys.path = sys_path
        sys.argv = sys_argv


def get_local_modules(path_prefix):
    """
    return module names loaded from a path with path_prefix

    :param path_prefix:
    :return:
    """
    return set(
        mod_name
        for mod_name, module in sys.modules.items()
        if getattr(module, "__file__", None)
        and module.__file__.startswith(path_prefix)
    )
