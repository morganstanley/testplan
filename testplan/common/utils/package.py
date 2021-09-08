import importlib
import sys
import threading
from contextlib import contextmanager

from testplan.common.utils.path import pwd

MOD_LOCK = threading.Lock()


@contextmanager
def import_tmp_module(module, path=None):
    module_imported = False

    with MOD_LOCK:
        if path is not None:
            # note: avoid adding "." to sys.path, mod won't have correct __file__
            # add "" to sys.path instead
            sys.path.insert(0, path)

        if module not in sys.modules:
            module_imported = True

        mod = importlib.import_module(module)

    yield mod

    with MOD_LOCK:
        if module_imported:
            del sys.modules[module]

        if path is not None:
            sys.path.remove(path)
