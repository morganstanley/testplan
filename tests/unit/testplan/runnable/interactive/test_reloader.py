"""Unit tests for the reloader module."""

import io
import modulefinder
import os
import sys
import time
from contextlib import contextmanager
from unittest import mock

import pytest

from testplan.common.utils import logger
from testplan.runnable.interactive import reloader
from testplan.testing import multitest


@multitest.testsuite
class Suite:
    """An example test suite to be reloaded."""

    @multitest.testcase
    def case_1(self, env, result):
        """Assert true"""
        result.true(True)

    @multitest.testcase
    def case_2(self, env, result):
        """Assert false"""

        result.false(False)

    @multitest.testcase
    def case_3(self, env, result):
        """Oops we failed"""
        result.fail("oops")

    @multitest.suite.skip_if(lambda testsuite: True)
    @multitest.testcase
    def case_skipped(self, env, result):
        """Oops we failed"""
        result.log("Skipped.")


# Mapping of module name to filepath and a list of owned objects for the mocked
# modules we will be "reloading".
MOCK_MOD_DIR = os.path.abspath(os.path.join(os.sep, "path", "to"))
MOCK_MODULES = {
    "__main__": os.path.join(MOCK_MOD_DIR, "main.py"),
    "mod_a": os.path.join(MOCK_MOD_DIR, "mod_a.py"),
    "mod_b": os.path.join(MOCK_MOD_DIR, "mod_b.py"),
    "mod_c": os.path.join(MOCK_MOD_DIR, "mod_c.py"),
    "mod_d": os.path.join(MOCK_MOD_DIR, "mod_d.py"),
}

# Mapping of module name to a list of attributes to set on that module. For
# simplicity we just assign a single test suite to mod_a.
MODULE_ATTRS = {"mod_a": [Suite]}


class MockModule:
    """Mock object to return in place of a real python module."""

    def __init__(self, name, filepath, attributes):
        self.__name__ = name
        self.__file__ = filepath
        for attr in attributes:
            setattr(self, attr.__name__, attr)

    def __repr__(self):
        return "MockModule[{}]".format(self.__name__)


# Mock for `sys.modules`, which are searched to find the modules that need
# reloading. PyTest will inspect `sys.modules` to do its magic so we extend
# a copy of the real `sys.modules` rather than just creating a totally bogus
# new one.
MOCK_SYSMODULES = sys.modules.copy()
MOCK_SYSMODULES.update(
    {
        name: MockModule(name, filepath, MODULE_ATTRS.get(name, []))
        for name, filepath in MOCK_MODULES.items()
    }
)

# Mapping of module name to a `modulefinder.Module` object, which is used by
# the `modulefinder` module to store metadata about a module - e.g. its name,
# filepath and the names of its attributes.
MOCK_MODULEFINDER_MODS = {
    name: modulefinder.Module(name, file=filepath)
    for name, filepath in MOCK_MODULES.items()
}


def _set_module_globals():
    """
    Set the `globalnames` attribute on the mocked `modulefinder` modules, and
    set the __module__ attribute on each attribute to match its owning module.

    WARNING: this function mutates MOCK_MODULEFINDER_MODS, it should only be
    called once.
    """
    for mod_name, mod in MOCK_MODULEFINDER_MODS.items():
        for attr in MODULE_ATTRS.get(mod_name, []):
            mod.globalnames[attr.__name__] = 1
            attr.__module__ = mod_name


_set_module_globals()
del _set_module_globals


class MockModuleFinder:
    """
    Mock ModuleFinder object. Allows us to control the structure of discovered
    module dependencies.
    """

    def __init__(self, path):
        del path  # Unused
        self.modules = {}
        self._curr_mod = None

    def load_module(self, fqname, fp, pathname, file_info):
        """
        Don't actually run any script - just call the expected hooks to
        simulate the dependency structure we want.
        """
        self.modules = MOCK_MODULEFINDER_MODS

        self.import_hook("mod_a", self.modules["__main__"])
        self.import_hook("mod_b", self.modules["__main__"])
        # self.import_hook("mod_b", self.modules["mod_a"])
        self.import_hook("mod_c", self.modules["mod_a"])
        self.import_hook("mod_d", self.modules["mod_a"])
        self.import_hook("mod_d", self.modules["mod_b"])

    def import_hook(self, name, caller=None, *args, **kwargs):
        self._curr_mod = self.modules[name]
        self.import_module()

    def import_module(self, *args, **kwargs):
        curr_mod = self._curr_mod
        self._curr_mod = None
        return curr_mod


@pytest.fixture
def mock_reload_env():
    """Set up the mock environment for unit-testing the reloader module."""
    # For unmodified files, just return a fake stat result with everything set
    # to 0.
    unmodified_stat_result = os.stat_result(0 for _ in range(10))

    # For modified files, set the st_mtime to 1 day in the future. It doesn't
    # matter that the modification time is in the future - just so long as it
    # is greater than the current time. The reloader only checks st_mtime,
    # which is the value at the 8th index passed to os.stat_result.
    one_day_hence = time.time() + 24 * 60 * 60
    modified_stat_result = os.stat_result(
        0 if i != 8 else one_day_hence for i in range(10)
    )

    @contextmanager
    def mock_open(file, mode="r", **kwargs):
        yield io.StringIO("")

    def mock_stat(filepath):
        if filepath in mock_stat.modified_files:
            return modified_stat_result
        else:
            return unmodified_stat_result

    mock_stat.modified_files = set()

    with (
        mock.patch("io.open", new=mock_open),
        mock.patch("os.stat", new=mock_stat),
        mock.patch("sys.modules", new=MOCK_SYSMODULES),
        mock.patch("modulefinder.ModuleFinder", new=MockModuleFinder),
        mock.patch(
            "importlib.reload", side_effect=lambda module: module
        ) as mock_reload,
    ):
        # Despite mocking modulefinder.ModuleFinder above, we also need to
        # swap out the real ModuleFinder with our mock one in the list of
        # bases for the GraphModuleFinder.
        old_bases = reloader._GraphModuleFinder.__bases__
        try:
            reloader._GraphModuleFinder.__bases__ = (
                MockModuleFinder,
                logger.Loggable,
            )
            reload_obj = reloader.ModuleReloader()

            yield reload_obj, mock_reload, mock_stat
        finally:
            reloader._GraphModuleFinder.__bases__ = old_bases


def test_dependency_reload(mock_reload_env):
    r"""
    Test reload of dependencies. We set up a module dependency structure
    modules main and A, B, C and D that looks like:

                                    main
                                   /    \
                                  /      \
                                 V       V
                                 A        B
                                / \        \
                               /   ---      \
                              V       |     V
                             C        --->  D

    We then test making modifications to each of A, B, C and D in turn to
    check that the expected modules are reloaded in the correct order.
    """
    reload_obj, mock_reload, mock_stat = mock_reload_env

    # First we check that the dependency graph was built as expected.
    _check_dep_graph(reload_obj._dep_graph)

    # Now reload the dependencies. Since no files have been modified,
    # nothing should be reloaded. Note that we do not specify any test
    # instances - for now we are just testing the module reload behaviour,
    # not the updating of test instances.
    reload_obj.reload(tests=[])
    mock_reload.assert_not_called()

    # Now let's say we modify mod_a. Only mod_a needs reloading.
    mock_stat.modified_files = {MOCK_MODULES["mod_a"]}
    reload_obj.reload(tests=[])
    mock_reload.assert_called_once_with(MOCK_SYSMODULES["mod_a"])

    # Now modify mod_b instead. Only mod_a needs reloading.
    mock_stat.modified_files = {MOCK_MODULES["mod_b"]}
    mock_reload.reset_mock()
    reload_obj.reload(tests=[])
    mock_reload.assert_called_once_with(MOCK_SYSMODULES["mod_b"])

    # Now modify mod_c. Both C and A should be reloaded.
    mock_stat.modified_files = {MOCK_MODULES["mod_c"]}
    mock_reload.reset_mock()
    reload_obj.reload(tests=[])
    mock_reload.assert_has_calls(
        [
            mock.call(MOCK_SYSMODULES["mod_c"]),
            mock.call(MOCK_SYSMODULES["mod_a"]),
        ]
    )

    # Now modify mod_d. We expect to reload module D first, then A, then B.
    mock_stat.modified_files = {MOCK_MODULES["mod_d"]}
    mock_reload.reset_mock()
    reload_obj.reload(tests=[])
    mock_reload.assert_has_calls(
        [
            mock.call(MOCK_SYSMODULES["mod_d"]),
            mock.call(MOCK_SYSMODULES["mod_a"]),
            mock.call(MOCK_SYSMODULES["mod_b"]),
        ]
    )


def test_test_refresh(mock_reload_env):
    """Test that tests are correctly refreshed after a module is reloaded."""
    reload_obj, mock_reload, mock_stat = mock_reload_env

    # Modify mod_a again. This time we specify a MultiTest to refresh
    # suites for.
    mock_reload.reset_mock()
    test = multitest.MultiTest(name="MTest", suites=[Suite()])
    test.cfg.suites[0].__module__ = "mod_a"
    mock_stat.modified_files = {MOCK_MODULES["mod_a"]}

    reload_obj.reload(tests=[test])
    mock_reload.assert_called_once_with(MOCK_SYSMODULES["mod_a"])


def _check_dep_graph(dep_graph):
    """
    Check that the dependency graph generated by the reload module is as
    expected. Since we control the order of import hooks the ordering of the
    dependencies in the graph should be fully deterministic.
    """
    # Check that the expected graph of modules is produced. Due to
    # limitations in rendering the dependency graph as a string, you will
    # notice that mod_b and mod_d appear multiple times in the string. We
    # check below to confirm that the nodes are the same object.
    assert (
        dep_graph.graph_string
        == """__main__ ->
  mod_a ->
    mod_c
    mod_d
  mod_b ->
    mod_d"""
    )

    # Check mod_a
    assert dep_graph.dependencies[0].name == "mod_a"

    # Check mod_b
    assert dep_graph.dependencies[1].name == "mod_b"

    # Check mod_c
    assert dep_graph.dependencies[0].dependencies[0].name == "mod_c"

    # Check mod_d
    assert dep_graph.dependencies[0].dependencies[1].name == "mod_d"
    assert (
        dep_graph.dependencies[0].dependencies[1]
        is (dep_graph.dependencies[1].dependencies[0])
    )
