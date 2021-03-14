import os
import re
import runpy
import sys
from traceback import format_exc

import pytest

from testplan.common.utils.path import change_directory

import platform

SUCCES_EXIT_CODES = (
    0,
    False,
    None,
)  # these considerd as 0 return value and means success

_FILE_DIR = os.path.dirname(__file__)

# This file is under tests/functional/examples, so the root directory is 3
# levels up.
_REPO_ROOT = os.path.abspath(
    os.path.join(_FILE_DIR, *(os.pardir for _ in range(3)))
)
_EXAMPLES_ROOT = os.path.join(_REPO_ROOT, "examples")

ON_WINDOWS = platform.system() == "Windows"

KNOWN_EXCEPTIONS = [
    r"TclError: Can't find a usable init\.tcl in the following directories:",  # Matplotlib module improperly installed. Will skip Data Science example.
    r"ImportError: lib.*\.so\..+: cannot open shared object file: No such file or directory",  # Matplotlib module improperly installed. Will skip Data Science example.
    r"ImportError: No module named sklearn.*",  # Missing module sklearn. Will skip Data Science example.
    r"ImportError: No module named Tkinter",  # Missing module Tkinter. Will skip Data Science example.
    r"ImportError: No module named _tkinter.*",  # Missing module Tkinter. Will skip Data Science example.
    r"RuntimeError: Download pyfixmsg library .*",  # Missing module pyfixmsg. Will skip FIX example.
    r"No spec file set\. You should download .*",  # Missing FIX spec file. Will skip FIX example.
    r"RuntimeError: You need to compile test binary first.",  # Need to compile cpp binary first. Will skip GTest example.
    r"FATAL ERROR: Network error: Connection refused",  # We don't fail a pool test for connection incapability.
    r"lost connection",
    r"RuntimeError: Testcase raises",  # Expected error raised by PyUnit example.
]

SKIP = [
    os.path.join("ExecutionPools", "Remote", "test_plan.py"),
    os.path.join("Interactive", "Basic", "test_plan.py"),
    os.path.join("Interactive", "Environments", "test_plan.py"),
    os.path.join("ExecutionPools", "Treadmill", "test_plan.py"),
    os.path.join("Data Science", "basic_models", "test_plan.py"),
    os.path.join("Data Science", "overfitting", "test_plan.py"),
    # The FXConverter example is currently unstable - re-enable when fixed.
    os.path.join("App", "FXConverter", "test_plan.py"),
    os.path.join(
        "Multitest", "Listing", "Custom Listers", "test_plan_command_line.py"
    ),
]

SKIP_ON_WINDOWS = [
    os.path.join("Cpp", "GTest", "test_plan.py"),
    os.path.join("Cpp", "Cppunit", "test_plan.py"),
    os.path.join("Cpp", "HobbesTest", "test_plan.py"),
    os.path.join("Transports", "FIX", "test_plan.py"),
    os.path.join("App", "Basic", "test_plan.py"),
]


def _param_formatter(param):
    if "examples" in param:
        return repr(param.rsplit("examples")[1])
    return repr(param)


@pytest.mark.parametrize(
    "root,filename",
    [
        (os.path.abspath(root), filename)
        for root, _, files in os.walk(_EXAMPLES_ROOT, followlinks=True)
        for filename in files
        if ("test_plan" in filename and filename.endswith(".py"))
    ],
    ids=_param_formatter,
)
def test_example(root, filename):
    file_path = os.path.join(root, filename)

    if ON_WINDOWS and any(
        [file_path.endswith(skip_name) for skip_name in SKIP_ON_WINDOWS]
    ):
        pytest.skip()
    elif any([file_path.endswith(skip_name) for skip_name in SKIP]):
        pytest.skip()

    try:

        # set up like an external invocation.
        # add current dir to fron of sys path
        # no arguments pass in command line

        sys.path.insert(0, root)
        argv = sys.argv
        sys.argv = [sys.argv[0]]

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
        for exception in KNOWN_EXCEPTIONS:
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
