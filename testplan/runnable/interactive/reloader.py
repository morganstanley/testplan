"""Interactive code reloader module."""

import sys
import os
import io
import time
import inspect
import importlib
import modulefinder
import collections
import functools
import warnings

from testplan.common.utils import path as path_utils
from testplan.common.utils import logger
from testplan.common.utils import strings
from testplan.common.utils.package import import_tmp_module
from testplan.testing.multitest import suite, MultiTest


class ModuleReloader(logger.Loggable):
    """
    Reloads modules and their dependencies if there was any file modification.

    :param extra_deps: Modules to register as extra dependencies to reload,
        despite not being directly imported by __main__, or paths of these
        modules.
    :type extra_deps: ``Iterable[ModuleType]`` or ``Iterable[str]``
    :param scheduled_modules: Name of module which has schedule tests, with
        the module path registered as extra dependencies to reload.
    :type scheduled_modules: ``Dict[str, str]``
    """

    def __init__(self, extra_deps=None, scheduled_modules=None):
        super(ModuleReloader, self).__init__()

        self._extra_deps = extra_deps or []
        self._scheduled_modules = scheduled_modules or {}

        if isinstance(self._scheduled_modules, (tuple, list)):
            counter = collections.Counter(
                module_info[0] for module_info in self._scheduled_modules
            )
            duplicates = [mod for mod, cnt in counter.items() if cnt > 1]
            for dup in duplicates:
                paths = set(
                    os.path.realpath(path)
                    for mod, path in self._scheduled_modules
                    if mod == dup
                )
                if len(paths) > 1:
                    paths_to_print = os.linesep.join(
                        f"  -- {path}" for path in paths
                    )
                    warnings.warn(
                        f"Module `{dup}` imported from different places, it"
                        " makes Testplan not able to reload tests properly:"
                        f"{os.linesep}{paths_to_print}"
                    )
            self._scheduled_modules = dict(self._scheduled_modules)

        # Import modules that have scheduled tests
        for mod, path in self._scheduled_modules.items():
            with import_tmp_module(
                mod, path, delete=False, warn_if_exist=False
            ):
                pass

        (
            self._reload_dirs,
            self._dep_graph,
            self._watched_modules,
        ) = self._build_dependencies()

        # Last recorded reload time for watched modules.
        self._last_reload_time = {}  # type: Dict[str, float]
        self._init_time = time.time()

    def reload(self, tests, rebuild_dependencies=False):
        """
        Reload code and update testsuites in given tests with new code.

        :param tests: Iterable of Tests (e.g. MultiTest).
        :type tests: ``Iterable[Test]``
        :param rebuild_dependencies: Hard re-calculate all file dependencies.
        :type rebuild_dependencies: ``bool``
        """
        start_time = time.time()
        suite_instances = self._suites_by_class(tests)

        if rebuild_dependencies:
            (
                self._reload_dirs,
                self._dep_graph,
                self._watched_modules,
            ) = self._build_dependencies()

        modified_modules = self._modified_modules
        if modified_modules:
            self.logger.debug(
                "Watched files have been modified - reloading dependencies."
            )
            self._reload_modified_modules(modified_modules, suite_instances)
            self.logger.info(
                "Took %.2f seconds to reload dependencies.",
                time.time() - start_time,
            )
        else:
            self.logger.debug("No watched files have been modified.")

    def _build_dependencies(self):
        """
        Build a list of directories to reload code from and a tree of
        dependencies.
        """
        main_module_file = sys.modules["__main__"].__file__
        if not main_module_file:
            raise RuntimeError(
                "Can only use interactive reloader when the __main__ module "
                "is a file."
            )

        reload_dirs = {os.path.abspath(os.path.dirname(main_module_file))}

        # Add extra reload source directories if required.
        reload_dirs = reload_dirs.union(
            self._extra_reload_dirs(
                self._extra_deps + list(set(self._scheduled_modules.values()))
            )
        )

        dep_graph, watched_modules = self._build_dep_graph(
            main_module_file, reload_dirs
        )

        return reload_dirs, dep_graph, watched_modules

    def _extra_reload_dirs(self, deps):
        """
        Build and return a set of reload directories used by extra
        dependencies.

        :param deps: Extra modules to add as dependencies of __main__.
        :type deps ``Iterable[ModuleType]``
        :return: Reload directories of extra dependencies
        :rtype: ``set[str]``
        """
        reload_dirs = set()

        for dep in deps:
            if isinstance(dep, str):
                dirpath = path_utils.fix_home_prefix(os.path.abspath(dep))
                # Add it to `sys.path` for reloading
                if dirpath not in sys.path:
                    sys.path.append(dirpath)
                self.logger.debug("Adding extra dependent path: %s", dirpath)
                reload_dirs.add(dirpath)
            else:
                filepath = _module_filepath(dep)
                dirpath = os.path.dirname(filepath) if filepath else None

                # Find the path where module or package can be imported
                if _has_package(dep):
                    package = sys.modules.get(dep.__package__.split(".")[0])
                    if package is not None:
                        filepath = _module_filepath(package)
                        if filepath:
                            dirpath = os.path.dirname(
                                os.path.dirname(filepath)
                            )
                if dirpath:
                    # Even though this module has been imported, its directory
                    # may have been removed from `sys.path`. In that case it
                    # needs to be added back so the module can be reloaded.
                    if dirpath not in sys.path:
                        sys.path.append(dirpath)
                    self.logger.debug(
                        "Adding extra dependent path for module %s: %s",
                        dep.__name__,
                        dirpath,
                    )
                    reload_dirs.add(dirpath)

        return reload_dirs

    def _build_dep_graph(self, main_module_file, reload_dirs):
        """
        Build the graph of dependencies starting from the main module.

        :param main_module_file: File path to the python script being executed
            as __main__.
        :type main_module_file: ``str``
        :param reload_dirs: Directories to reload modules from.
        :type reload_dirs: ``Iterable[str]``
        """
        finder = _GraphModuleFinder(path=self._filtered_syspath(reload_dirs))

        try:
            with io.open(main_module_file, "r") as fp:
                text = fp.read()
        except OSError as exc:
            raise RuntimeError(
                "Could not run main module {} as a script: {}.".format(
                    main_module_file,
                    exc,
                )
            )
        else:
            imports = "".join(
                f"import {module_name}{os.linesep}"
                for module_name in sorted(self._scheduled_modules.keys())
            )
            finder.load_module(
                "__main__",
                io.StringIO(  # Instance of `TextIOBase` with a `read` method
                    text + os.linesep * 2 + imports if imports else text
                ),
                main_module_file,
                ("", "r", 1),  # In deprecated module `imp`: PY_SOURCE == 1
            )

        return finder.build_dep_graph()

    def _filtered_syspath(self, reload_dirs):
        """
        :return: sys.path filtered by paths that are in a reload dir.
        :rtype: ``List[str]``
        """
        return list(
            {
                path
                for path in sys.path
                if any(
                    os.path.abspath(path).startswith(os.path.abspath(d))
                    for d in reload_dirs
                )
            }
        )

    @property
    def _modified_modules(self):
        """
        Calls `os.stat` on all watched files to check which ones have been
        modified and require a reload.

        :return: Set of all modules whose filepaths that have been modified
            and require reloading.
        :rtype: ``set[_ModuleNode]``
        """
        return set(
            mod
            for mod in self._watched_modules
            if os.stat(mod.filepath).st_mtime
            > self._last_reload_time.get(mod.name, self._init_time)
        )

    def _suites_by_class(self, tests):
        """
        Creates a {module_name: {class_name: [suite_instance, ...]}} mapping.

        :param tests: iterator of Tests.
        :type tests: ``Iterable[Test]``
        :return: Mapping of module and class name to list of suite instances.
        :rtype: ``Dict[str, Dict[str, List[Any]]]``
        """
        suite_dict = collections.defaultdict(
            functools.partial(collections.defaultdict, list)
        )
        for test in tests:
            if isinstance(test, MultiTest):
                for suite in test.cfg.suites:
                    suite_dict[suite.__module__][
                        suite.__class__.__name__
                    ].append(suite)
        return suite_dict

    def _reload_modified_modules(self, modified_modules, suite_instances):
        """
        Reload all files that have been modified. If a module has been reloaded,
        all modules that depend on it should also be reloaded. We ensure this
        by walking the graph of dependencies in depth-first order.

        :param modified_modules: Set of modules that have been modified and
            require a reload.
        :type modified_modules: ``set[_ModuleNode]``
        :param suite_instances: Mapping of module and class names to list of
            suite instances.
        :type suite_instances: ``Dict[str, Dict[str, List[Any]]]``
        """
        # Walk the graph using depth-first search order.
        visited_nodes = set()
        reloaded_nodes = set()

        # We never want to reload the __main__ module, so we start the
        # recursion from each immediate dependency in turn.
        for dep in self._dep_graph.dependencies:
            if dep not in visited_nodes:
                self._reload_recur(
                    dep,
                    modified_modules,
                    suite_instances,
                    visited_nodes,
                    reloaded_nodes,
                )

    def _reload_recur(
        self,
        mod_node,
        modified_modules,
        suite_instances,
        visited_nodes,
        reloaded_nodes,
    ):
        """
        Recursively walk the graph of dependencies, reloading all modified
        files.

        :param mod_node: Current module we are processing.
        :type mod_node: ``_ModuleNode``
        :param modified_modules: Set of modules that have been modified and
            require a reload.
        :type modified_modules: ``set[_ModuleNode]``
        :param suite_instances: Mapping of module and class names to list of
            suite instances.
        :type suite_instances: ``Dict[str, Dict[str, List[Any]]]``
        :param visited_nodes: Set of modules already visited.
        :type visited_nodes: ``set[_ModuleNode]``
        :return: Whether the module was reloaded.
        :rtype: ``bool``
        """

        if mod_node in reloaded_nodes:
            return True  # we already reloaded this
        if mod_node in visited_nodes:
            return False  # we already decided not need reload

        visited_nodes.add(mod_node)

        # Reload this module's dependencies if necessary. Check if any
        # dependencies were reloaded - we will need to reload our current
        # module too if so. Note that we must use a list comprehension inside
        # the any call to avoid short-circuiting as soon as a dependency is
        # reloaded.

        dep_reloaded = any(
            [
                self._reload_recur(
                    dep,
                    modified_modules,
                    suite_instances,
                    visited_nodes,
                    reloaded_nodes,
                )
                for dep in mod_node.dependencies
            ]
        )

        # Reload this module if there are file modifications or if any of its
        # dependencies have been reloaded.
        if mod_node in modified_modules or dep_reloaded:
            self.logger.info("Reloading %s", mod_node.name)
            mod_node.reload()
            if mod_node.name in suite_instances:
                mod_node.update_suites(suite_instances)
            self._last_reload_time[mod_node.name] = time.time()
            reloaded_nodes.add(mod_node)
            return True
        else:
            return False


class _GraphModuleFinder(modulefinder.ModuleFinder, logger.Loggable):
    r"""
    Variant of the standard library ModuleFinder that is able to produce a
    directed acyclic graph of dependencies. The root node corresponds to the
    main module passed as a script, its child nodes correspond to its
    direct import dependencies, and so on.

    An example of how such a graph
    with a main module and dependencies A, B, C and D could look is:

                                    main
                                   /    \
                                  /      \
                                 V       V
                                 A ----> B
                                / \        \
                               /   ---     \
                              V       |    V
                              C        --> D

    :param args: passed to ModuleFinder
    :param kwargs: passed to ModuleFinder
    """

    def __init__(self, *args, **kwargs):
        # In the Python 2 stdlib, ModuleFinder is an old-style class that
        # does not inherit from object, therefore we cannot use super().
        modulefinder.ModuleFinder.__init__(self, *args, **kwargs)
        logger.Loggable.__init__(self)  # Enable logging via self.logger

        # Mapping of module object to a set of its dependencies. We store the
        # dependencies in a list instead of a set to preserve ordering. While
        # not strictly necessary, it makes testing easier when the ordering
        # of nodes in the graph can be relied on. However, we must ensure that
        # each dependency is unique, so we check before adding each new
        # dependency below. This should be a significant performance issue,
        # as we only expect each module to have a relatively small number
        # of dependencies (around 10s) so O(n) adding is acceptable.
        self._module_deps = collections.defaultdict(list)
        self._curr_caller = None
        self._module_nodes = {}

    def import_hook(self, name, caller=None, *args, **kwargs):
        """
        Hook called when ``caller`` imports module ``name``. Store off the
        caller so we can use it later.

        :param name: Name of the module being imported.
        :type name: ``str``
        :param caller: Module object that is importing ``name``.
        :type caller: ``modulefinder.Module``
        :param args: Other args are passed down to
            ``modulefinder.ModuleFinder.import_hook``
        :param kwargs: Other kwargs are passed down to
            ``modulefinder.ModuleFinder.import_hook``
        :return: Return value from ``modulefinder.ModuleFinder.import_hook``
        """
        previous_caller = self._curr_caller

        if caller is None:
            caller_frame = inspect.stack()[2]
            self._curr_caller = caller_frame.frame.f_locals.get("m")
            assert (
                self._curr_caller is not None
            ), "Source code of `modulefinder` library has changed !!"
        else:
            self._curr_caller = caller

        mod = modulefinder.ModuleFinder.import_hook(
            self, name, caller, *args, **kwargs
        )
        self._curr_caller = previous_caller

        return mod

    def import_module(self, *args, **kwargs):
        """
        Called a bit further down the stack when a module is imported. Update
        the internal mapping of module dependencies.

        :param args: all args are passed down to
            ``modulefinder.ModuleFinder.import_module``
        :param kwargs: all kwargs are passed down to
            ``modulefinder.ModuleFinder.import_module``
        :return: Imported module object.
        :rtype: ``modulefinder.Module``
        """
        caller = self._curr_caller
        mod = modulefinder.ModuleFinder.import_module(self, *args, **kwargs)

        if (
            caller is not None
            and mod is not None
            and _has_file(mod)
            and mod not in self._module_deps[caller]
        ):
            self.logger.debug(
                "Adding %(mod)s to %(caller)s's dependencies",
                {"mod": mod.__name__, "caller": caller.__name__},
            )
            self._module_deps[caller].append(mod)

        return mod

    def build_dep_graph(self):
        """
        Build a directed graph of dependencies, made up of ``_ModuleNode``s.

        :return: Root node of dependency graph and a set of all nodes in the
            graph.
        :rtype: ``Tuple[_ModuleNode, set[_ModuleNode]``
        """
        main_mod = self.modules["__main__"]
        root_node = self._produce_graph(main_mod, [])
        return root_node, set(self._module_nodes.values())

    def _produce_graph(self, mod, processed):
        """
        Recursive function to build a graph of dependencies.

        :param mod: Module to use for the tree root.
        :type mod: ``modulefinder.Module``
        :param processed: List of modules processed so far in this branch, in
            order of processing. Used to avoid infinite recursion in the case
            of circular dependencies.
        :type processed: ``List[modulefinder.Module]``
        :raises RuntimeError: If ``mod`` is in ``processed`` - the calling
            function should ensure it is not asking to process a module that
            has already been processed.
        :return: Root node of dependency graph.
        :rtype: ``_ModuleNode``
        """
        self.logger.debug(
            "Creating node in dependency graph for module %s", mod.__name__
        )

        if mod in processed:
            raise RuntimeError(
                "Module {mod} has already been processed in this branch. "
                "Already processed = {processed}".format(
                    mod=mod.__name__, processed=processed
                )
            )

        # Create a new list of processed modules to avoid mutating the list
        # we were passed.
        new_processed = processed + [mod]

        # If this module has already been processed in another branch, we
        # can short circuit and return the existing node.
        if mod in self._module_nodes:
            return self._module_nodes[mod]

        # Now for the recursive step - produce a sub-graph of the dependencies
        # of each of our dependencies first, then attach each one to the set
        # of dependencies for the current node. Check that each dependency
        # has not already been processed in this branch to avoid circular
        # dependencies causing infinite recursion.
        dependencies = [
            self._produce_graph(mod=dep, processed=new_processed)
            for dep in self._module_deps[mod]
            if dep not in new_processed
        ]
        node = _ModuleNode(mod, dependencies)
        self._module_nodes[mod] = node
        return node


class _ModuleNode:
    """
    Node in the directed acyclic graph of dependencies produced by
    _GraphModuleFinder.

    :param mod: Module object this node represents
    :type mod: ``modulefinder.Module``
    :param dependencies: List of nodes for modules this node is dependent on.
    :type dependencies: ``List[_ModuleNode]``
    """

    def __init__(self, mod, dependencies):
        self.mod = mod
        if not all(isinstance(d, self.__class__) for d in dependencies):
            raise TypeError(
                "Dependencies must all be of type {}".format(self.__class__)
            )
        self.dependencies = dependencies
        self.filepath = _module_filepath(mod)
        self._native_mod = None

    def __repr__(self):
        return "ModuleNode[{}]".format(self.name)

    def __hash__(self):
        return hash(self.mod)

    @property
    def graph_string(self):
        """
        :return: a multi-line string representing the graph from this node
            downwards.
        :rtype: ``str``
        """
        if self.dependencies:
            ret_str = "{mod} ->\n{children}".format(
                mod=self.name,
                children=strings.indent(
                    "\n".join(c.graph_string for c in self.dependencies)
                ),
            )
        else:
            ret_str = self.name

        return ret_str

    @property
    def name(self):
        return self.mod.__name__

    def reload(self):
        """Reload this module from file."""
        try:
            if self._native_mod is None:
                self._native_mod = sys.modules[self.mod.__name__]
            self._native_mod = importlib.reload(self._native_mod)
        except (KeyError, ModuleNotFoundError):
            # ignore dynamic import module
            pass

    def update_suites(self, suite_instances):
        """
        Update suite objects to new classes.

        :param suite_instances: Mapping of module and class name to test suite
            instances.
        :type suite_instances: ``Dict[str, Dict[str, List[Any]]``
        """
        for suite_cls in self._iter_suites():
            for suite_obj in suite_instances[self.name].get(
                suite_cls.__name__, []
            ):
                suite_obj.__class__ = suite_cls
                suite.set_testsuite_testcases(suite_obj)

    def _iter_suites(self):
        """Generate classes of test suites defined in this module."""
        for key in self.mod.globalnames.keys():
            attr = getattr(self._native_mod, key, None)
            if attr and _is_testsuite(attr):
                yield attr


def _has_file(mod):
    """
    :param mod: Module object. Can be any of the multiple types used to
        represent a module, we just check for a __file__ attribute.
    :type mod: ``Any``
    :return: If given module has a not None __file__ attribute.
    :rtype: ``bool``
    """
    return hasattr(mod, "__file__") and mod.__file__ is not None


def _has_package(mod):
    """
    :param mod: Module object. Can be any of the multiple types used to
        represent a module, we just check for a __package__ attribute.
    :type mod: ``Any``
    :return: If given module has a valid __package__ attribute.
    :rtype: ``bool``
    """
    return hasattr(mod, "__package__") and mod.__package__ != ""


def _module_filepath(mod):
    """
    :param mod: Module object - either a module itself of its modulefinder
        proxy.
    :type mod: ``Union[module, modulefinder.module]``
    :return: the normalised filepath to a module, or None if it has no __file__
        attribute.
    :rtype: ``Optional[str]``
    """
    if not _has_file(mod):
        return None

    ret_path = path_utils.fix_home_prefix(os.path.abspath(mod.__file__))
    if ret_path.endswith("c"):
        return ret_path[:-1]

    return ret_path


def _is_testsuite(attr):
    """
    :return: If given attribute is a testsuite class.
    :rtype: ``bool``
    """
    return inspect.isclass(attr) and hasattr(attr, "__testcases__")
