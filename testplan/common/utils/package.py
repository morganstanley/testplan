import os
import sys
import importlib
import threading
import warnings
from contextlib import contextmanager

MOD_LOCK = threading.Lock()


@contextmanager
def import_tmp_module(module_name, path=None, delete=True, warn_if_exist=True):
    """
    Temporarily import a module by name and later remove all imported modules.

    :param module_name: Module name.
    :type module_name: ``str``
    :param path: Where the module can be imported.
    :type path: ``str`` or ``NoneType``
    :param delete: If delete imported modules from `sys.modules` after use.
    :type delete: ``bool``
    :param warn_if_exist: Warn if module name already exists in `sys.modules`.
    :type warn_if_exist: ``bool``
    """
    module = None
    modules_imported = []  # Names of imported modules

    with MOD_LOCK:
        if path is not None:
            if path == ".":
                path = ""
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            sys.path.insert(0, path)

        mod_name = ""
        for element in module_name.split("."):
            mod_name = f"{mod_name}.{element}" if mod_name else element
            if mod_name in sys.modules:
                if warn_if_exist:
                    warnings.warn(
                        f'Importing module: "{mod_name}" already loaded',
                    )
            else:
                modules_imported.append(mod_name)
            module = importlib.import_module(mod_name)

    yield module

    with MOD_LOCK:
        if delete:
            for mod_name in reversed(modules_imported):
                if mod_name in sys.modules:
                    del sys.modules[mod_name]

        if path is not None:
            sys.path.remove(path)
