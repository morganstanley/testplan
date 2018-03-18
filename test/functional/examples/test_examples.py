import os
import re
import sys
import subprocess
import pytest

from testplan.common.utils.path import change_directory

import platform

ON_WINDOWS = platform.system() == 'Windows'

KNOWN_EXCEPTIONS = [
    "TclError: Can't find a usable init\.tcl in the following directories:",
    "ImportError: No module named Tkinter",
    "ImportError: lib.*\.so\..+: cannot open shared object file: No such file or directory",
    "ImportError: No module named sklearn.*", # Missing lib sklearn. Will skip Data Science example.
    "ImportError: No module named _tkinter.*", # Missing module tkinder. Will skip Data Science example.
    "RuntimeError: Download pyfixmsg library .*", # Missing lib pyfixmsg. Will skip FIX example.
    "No spec file set\. You should download .*", # Missing FIX spec file. Will skip FIX example.
    "AttributeError: 'module' object has no attribute 'poll'",
    "RuntimeError: You need to compile test binary first." # Need to compile cpp binary first. Will skip GTest example.
]

SKIP_ON_WINDOWS = [
    os.path.join('Cpp', 'GTest', 'test_plan.py'),
]


def get_repo_root():
    cwd = os.getcwd()
    while True:
        contents = os.listdir(cwd)
        if 'testplan' in contents and os.path.isdir(
              os.path.join(cwd, 'testplan')):
            return cwd.split(os.sep)[-1]
        elements = cwd.split(os.sep)[:-1]
        if len(elements) < 2:
            raise RuntimeError('Could not find repo directory')
        cwd = os.sep.join(elements)


def _relative_dir(directory):
    cwd = os.getcwd()
    sub_dirs = cwd.rsplit(get_repo_root())[1]
    depth_from_root = sub_dirs.count(os.path.sep)
    path_args = [os.pardir] * depth_from_root + [directory]
    return os.path.join(*path_args)


def _param_formatter(param):
    if 'examples' in param:
        return repr(param.rsplit('examples')[1])
    return repr(param)


@pytest.mark.parametrize(
    'root,filename',
    [
        (os.path.abspath(root), filename)
        for root, _, files in os.walk(
            _relative_dir(os.path.join('testplan', 'examples')))
        for filename in files
        if 'test_plan' in filename
    ],
    ids=_param_formatter,
)
def test_example(root, filename):
    file_path = os.path.join(root, filename)

    if ON_WINDOWS and any(
        [file_path.endswith(skip_name) for skip_name in SKIP_ON_WINDOWS]
    ):
        pytest.skip()

    with change_directory(root), open(filename) as file_obj:
        first_line = file_obj.readline()
        try:
            subprocess.check_output(
                [
                    sys.executable,
                    filename
                ],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            out = e.output.decode()
            for exception in KNOWN_EXCEPTIONS:
                if re.search(exception, out):
                    pytest.skip()
            assert 'Exception in test_plan definition' not in out, \
                'Exception raised in test_plan definition.'
            assert 'Traceback (most recent call last):' not in out, \
                'Exception raised during test:\n{}'.format(out)
            assert \
                ('# This plan contains tests that demonstrate failures '
                 'as well.') == first_line.strip(), \
                "Expected \'{}\' example to pass, it failed.\n{}".format(
                    file_path,
                    out
                )
