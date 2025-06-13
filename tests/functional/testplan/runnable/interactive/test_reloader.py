"""Interactive reload tests."""

import importlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from pytest_test_filters import skip_on_windows

from testplan import runnable
from testplan.runnable.interactive import base
from testplan.runnable.interactive.reloader import _GraphModuleFinder
from testplan.runners.local import LocalRunner

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    "script_content, module_deps",
    (
        ("import outer", {"__main__": ("outer",)}),
        (
            "import outer.mod",
            {
                "__main__": ("outer", "outer.mod"),
            },
        ),
        (
            "from outer import mod",
            {
                "__main__": ("outer", "outer.mod"),
            },
        ),
        (
            "import outer.mod.VAL",
            {
                "__main__": ("outer", "outer.mod"),
            },
        ),
        (
            "from outer.mod import VAL",
            {
                "__main__": ("outer", "outer.mod"),
            },
        ),
        (
            "import outer.middle",
            {
                "__main__": ("outer", "outer.middle"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "from outer import middle",
            {
                "__main__": ("outer", "outer.middle"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "import outer.middle.mod",
            {
                "__main__": ("outer", "outer.middle", "outer.middle.mod"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "from outer.middle import mod",
            {
                # "outer.middle" imports "mod" internally
                "__main__": ("outer", "outer.middle"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "import outer.middle.mod.VAL",
            {
                "__main__": ("outer", "outer.middle", "outer.middle.mod"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "from outer.middle.mod import VAL",
            {
                "__main__": ("outer", "outer.middle", "outer.middle.mod"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "import outer.middle.inner",
            {
                "__main__": ("outer", "outer.middle", "outer.middle.inner"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "from outer.middle import inner",
            {
                # "outer.middle" imports "inner" internally
                "__main__": ("outer", "outer.middle"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "from outer.middle import *",
            {
                # In "__main__": "import *" cannot build dependency
                "__main__": ("outer", "outer.middle"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "import outer.middle.inner.mod1",
            {
                "__main__": (
                    "outer",
                    "outer.middle",
                    "outer.middle.inner",
                    "outer.middle.inner.mod1",
                ),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "from outer.middle.inner import mod1",
            {
                # "outer.middle.inner" imports "mod1" internally
                "__main__": ("outer", "outer.middle", "outer.middle.inner"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "import outer.middle.inner.mod2",
            {
                "__main__": (
                    "outer",
                    "outer.middle",
                    "outer.middle.inner",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "from outer.middle.inner import mod2",
            {
                # "outer.middle.inner" imports "mod2" internally
                "__main__": ("outer", "outer.middle", "outer.middle.inner"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "from outer.middle.inner.mod2 import *",
            {
                "__main__": (
                    "outer",
                    "outer.middle",
                    "outer.middle.inner",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "import outer.middle.extra",
            {
                "__main__": ("outer", "outer.middle", "outer.middle.extra"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "from outer.middle import extra",
            {
                # "outer.middle" imports "extra" internally
                "__main__": ("outer", "outer.middle"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        (
            "import outer.middle.extra import *",
            {
                # In "__main__": "import *" cannot build dependency
                "__main__": ("outer", "outer.middle"),
                "outer.middle": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.inner",
                    "outer.middle.mod",
                ),
                "outer.middle.inner": (
                    "outer",
                    "outer.middle",
                    "outer.middle.empty",
                    "outer.middle.inner.mod1",
                    "outer.middle.inner.mod2",
                ),
                "outer.middle.extra": (
                    "outer",
                    "outer.middle",
                    "outer.middle.extra",
                    "outer.middle.extra.mod1",
                    "outer.middle.extra.mod2",
                ),
            },
        ),
        # make sure loading namespace package won't raise exception
        (
            "import outer.namespace.mod1",
            {
                "__main__": ("outer",),
            },
        ),
    ),
)
def test_find_module(script_content, module_deps):
    """
    Check that `_GraphModuleFinder` utility can correctly build dependency
    graph between imported modules.

    We should verify that all import statements should be correctly traced
    and a dependency relationship between modules can be built. Consider
    these cases:
      -- import foo
      -- import foo.bar
      -- import foo.bar.VAL
      -- from foo import bar
      -- from foo.bar import VAL
      -- from foo.bar import *
      -- from . import bar     (inside foo)
      -- from .bar import VAL  (inside foo)
      -- from .bar import *    (inside foo)
      -- import foo.baz
      -- from .. import bar    (inside baz)

    So we design the various testcases to verify that we can correctly find
    dependency relationship among the packages and modules we are using.

    Some corner cases should be considered. In __init__.py file of a package,
    with or without imports in it, things can be different. A known example,
    when bar/__init__.py has "from . import qux" or "from .qux import sth",
    then `_GraphModuleFinder` gets difference result for 2 statements:
      -- import foo.bar.qux
      -- from foo.bar import qux

    Suppose you are importing "qux" in your "__main__" module, For the former,
    "__main__" directly depends on "foo", "foo.bar" and "foo.bar.qux", also,
    "foo.bar" depends on "foo.bar.qux", while for the latter, "__main__" only
    depends on "foo" and "foo.bar", it means "__main__" indirectly depends on
    "foo.bar.qux". Our `_GraphModuleFinder` is based on the standard library
    `modulefinder`, overrides its `import_hook` and `import_module` methods,
    refer to:
      -- https://github.com/python/cpython/blob/3.7/Lib/modulefinder.py#L214

    When importing "bar", the module "qux" will be loaded before "bar" is
    completely ready, thus "bar" should have an attribute called "qux", from
    the line above, we can know that when "__main__" loads "qux" from "bar",
    this piece of code is skipped and `import_module` method is not called,
    so, no direct dependency is built between "__main__" and "foo.bar.qux".
    Since that all direct/indirect dependencies will be recognized during
    reloading and our solution could work properly.

    An exception is that "from package import *" cannot always work. refer to:
      -- https://github.com/python/cpython/blob/3.7/Lib/modulefinder.py#L375

    All names represent * will be added into local namespace, however, no
    `import_module` is called and no direct dependency is built (although
    there might be indirect dependencies but that is not guaranteed). Just
    bear in mind that importing everything of a module is not encouraged
    in Python.
    """
    script_path = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False) as fp:
            fp.write(f"{script_content}\n")
            fp.flush()

        script_path = fp.name
        finder = _GraphModuleFinder(path=[THIS_DIRECTORY])

        try:
            finder.run_script(script_path)
        except OSError:
            raise RuntimeError(
                f"Could not run main module {script_path} as a script."
            )
        except Exception as err:
            print(err)
        else:
            if len(module_deps) > 0:
                assert len(finder._module_deps) == len(module_deps)
                for mod, deps in finder._module_deps.items():
                    assert module_deps[mod.__name__] == tuple(
                        sorted(dep.__name__ for dep in deps)
                    )
    finally:
        if script_path:
            os.remove(script_path)


def test_reload():
    """Tests reload functionality."""
    subprocess.check_call(
        [sys.executable, "interactive_executable.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )


def get_case_paths(case_num):
    dir = Path(__file__).parent / "reload_cases"
    return dir / f"case_{case_num}_prev.py", dir / f"case_{case_num}_curr.py"


def import_case_assertions(case_num):
    mod = importlib.import_module(
        f"tests.functional.testplan.runnable.interactive.reload_cases.case_{case_num}_assertions"
    )
    return getattr(mod, "prev_assertions"), getattr(mod, "curr_assertions")


@skip_on_windows(reason="Reloader won't work with pytest on Windows.")
@pytest.mark.parametrize("case_num", tuple(range(3)))
def test_reload_testcase_change(case_num):
    prev_path, curr_path = get_case_paths(case_num)
    prev_assertions, curr_assertions = import_case_assertions(case_num)

    with mock.patch("cheroot.wsgi.Server"):
        f = tempfile.NamedTemporaryFile("r+", delete=False, suffix=".py")
        try:
            shutil.copy(prev_path, f.name)
            runner = runnable.TestRunner(name="TestRunner", interactive_port=0)
            runner.add_resource(LocalRunner())
            runner.schedule_all(
                path=Path(f.name).parent, name_pattern=Path(f.name).name
            )
            irunner = base.TestRunnerIHandler(runner)
            irunner.run_all_tests()

            prev_assertions(irunner.report)

            shutil.copy(curr_path, f.name)
            irunner.reload(rebuild_dependencies=True)
            irunner.reload_report()

            curr_assertions(irunner.report)
        finally:
            os.unlink(f.name)
