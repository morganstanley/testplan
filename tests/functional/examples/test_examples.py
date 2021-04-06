import os

import pytest

import platform

from example_runner import run_example_in_process

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
    os.path.join("JUnit", "test_plan.py"),
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

    run_example_in_process(filename, root, KNOWN_EXCEPTIONS)
