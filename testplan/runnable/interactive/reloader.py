"""Interactive code reloader module."""

import os
import sys
import time
import inspect

from six.moves import reload_module

from modulefinder import ModuleFinder

from testplan.common.utils.path import fix_home_prefix, pwd
from testplan.testing.multitest import suite


def suites_by_class(tests):
    """Creates a {class --> [suite_instance, ...]} mapping."""
    suite_dict = {}
    for test in tests:
        try:
            for suite in test.cfg.suites:
                if suite.__class__ not in suite_dict:
                    suite_dict[suite.__class__] = []
                suite_dict[suite.__class__].append(suite)
        except:
            # No suites in test.
            pass
    return suite_dict


def _has_file(mod):
    """
    :return: If given module has a not None __file__ attribute.
    :rtype: ``bool``
    """
    return hasattr(mod, '__file__') and mod.__file__ is not None


def _is_testsuite(attr):
    """
    :return: If given attribute is a testsuite class.
    :rtype: ``bool``
    """
    return inspect.isclass(attr) and hasattr(attr, '__testcases__')


def _get_module_suites(module, suite_dict):
    """
    Get suite objects to update by class name (unique in one module).

    :param module: Module to search for test suites.
    :type module: ``types.ModuleType``
    :param suite_dict: Dict of test suites.
    :type suite_dict: ``Dict``
    :return: Dict of suites in the current module.
    :rtype: ``Dict``
    """
    module_suites = {}
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if _is_testsuite(attr):
            module_suites[attr.__name__] = suite_dict.get(attr, [])
    return module_suites


def _update_suites(module, module_suites):
    """
    Update suite objects to new classes.

    :param module: Module to update suite object for.
    :type module: ``types.ModuleType``
    :param module_suites: Suites in the corresponding module.
    :type module_suites: ``Dict``
    """
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if _is_testsuite(attr):
            for suite_obj in module_suites.get(attr.__name__, []):
                suite_obj.__class__ = attr
                suite.set_testsuite_testcases(suite_obj)


class ModuleReloader(object):
    """
    Reloads modules and their dependencies if there was any file modification.
    """
    def __init__(self, logger, extra_deps=None):
        self.logger = logger
        self._init_time = time.time()

        # Stores filepaths and their dependencies as per ModuleFinder.
        self._dependencies = {}

        # Filepath to module names map.
        self._files_to_modname = {}

        # Files to last modified timestamp.
        self._last_modified = {}

        # Source reload directories. Modules outside of these
        # will not be reloaded.
        self.reload_dirs = self._get_reload_dirs(extra_deps=extra_deps)

    @staticmethod
    def _module_filepath(filepath):
        ret_path = fix_home_prefix(os.path.abspath(filepath))
        if ret_path.endswith('c'):
            return ret_path[:-1]
        return ret_path

    def _get_reload_dirs(self, extra_deps=None):
        reload_dirs = []
        if _has_file(sys.modules['__main__']):
            main_module_file = self._module_filepath(
                sys.modules['__main__'].__file__)
            reload_dir = os.path.realpath(os.path.dirname(main_module_file))
        else:
            reload_dir = os.path.realpath(pwd())
        reload_dirs.append(fix_home_prefix(reload_dir))

        # Add extra reload source directories.
        for mod in extra_deps:
            module_file = self._module_filepath(mod.__file__)
            reload_dir = os.path.realpath(os.path.dirname(module_file))
            reload_dirs.append(fix_home_prefix(reload_dir))
        return reload_dirs

    def _build_dependencies(self):
        """
        Builds the dependency tree between the modules.
        """
        all_files = set()
        self._dependencies = {}
        self._files_to_modname = {}

        for name, mod in sys.modules.items():
            try:
                mod_filepath = self._module_filepath(
                    inspect.getfile(mod))
                if any(mod_filepath.startswith(directory)
                       for directory in self.reload_dirs):
                    all_files.add(mod_filepath)
                    self._files_to_modname[mod_filepath] = name
            except:
                pass

        for filepath in all_files:
            self._dependencies[filepath] = set()
            finder = ModuleFinder(path=self.reload_dirs)
            finder.run_script(filepath)

            for name, mod in finder.modules.items():
                if name == '__main__':
                    continue
                try:
                    mod_filepath = self._module_filepath(
                        inspect.getfile(sys.modules[name]))
                    if any(mod_filepath.startswith(directory)
                           for directory in self.reload_dirs):
                        self._dependencies[filepath].add(mod_filepath)
                except:
                    pass

        # Manipulating dependencies so that
        #   package/bob.py will not have package/__init__.py as dependency
        # but the other way round.
        for filepath in list(self._dependencies.keys()):
            modname = self._files_to_modname[filepath]
            for child in list(self._dependencies[filepath]):
                child_modname = self._files_to_modname[child]
                if modname.startswith(child_modname):
                    self._dependencies[filepath].remove(child)
                    self._dependencies[child].add(filepath)

    def _reload_deps(self, filepath, reloaded, suite_dict):
        """
        Reload all modules as per file changes and the dependency tree.
        """
        for child in self._dependencies[filepath]:
            if child in reloaded:
                continue
            self._reload_deps(child, reloaded, suite_dict)

        any_child_reloaded = any(
            child in reloaded for child in self._dependencies[filepath])

        last_modified = os.stat(filepath).st_mtime
        if filepath not in reloaded and \
              (any_child_reloaded or
                       last_modified != self._last_modified.get(filepath)):
            if self._files_to_modname[filepath] != '__main__':
                to_reload = sys.modules[self._files_to_modname[filepath]]
                module_suites = _get_module_suites(to_reload, suite_dict)
                reload_module(to_reload)
                _update_suites(to_reload, module_suites)
                self.logger.test_info('Reloaded module: {}'.format(
                    self._files_to_modname[filepath]))
                reloaded.add(filepath)
                self._last_modified[filepath] = last_modified
                return True
        return False

    def reload(self, tests, rebuild_dependencies=True):
        """
        Reload code and update testsuites in given tests with new code.

        :param tests: Test objects containing suites.
        :type tests: ``iterable``
        :param rebuild_dependencies: Hard re-calculate all file dependencies.
        :type rebuild_dependencies: ``bool``
        """
        suite_dict = suites_by_class(tests)

        if rebuild_dependencies is True:
            self._build_dependencies()

        reloaded = set()
        for filepath in self._dependencies:
            self._reload_deps(filepath, reloaded, suite_dict)
