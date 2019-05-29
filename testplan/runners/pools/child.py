"""
Child worker process entry point. This module is called as a script when
starting child worker processes.
"""

# Only stdlib imports can go here: we may be passed in the path to the
# testplan package and a dependencies module to load before testplan and
# third-party packages can be loaded.
import os
import sys
import time
import signal
import socket
import shutil
import inspect
import logging
import argparse
import platform
import threading
import subprocess


def parse_cmdline():
    """Child worker command line parsing"""
    parser = argparse.ArgumentParser(description='Remote runner parser')
    parser.add_argument('--address', action="store")
    parser.add_argument('--index', action="store")
    parser.add_argument('--testplan', action="store")
    parser.add_argument('--testplan-deps', action="store", default=None)
    parser.add_argument('--wd', action="store")
    parser.add_argument('--runpath', action="store", default=None)
    parser.add_argument('--type', action="store")
    parser.add_argument('--log-level',
                        action="store",
                        default=logging.DEBUG,
                        type=int)
    parser.add_argument('--remote-pool-type', action="store", default='thread')
    parser.add_argument('--remote-pool-size', action="store", default=1)

    return parser.parse_args()


if __name__ == '__main__':
    """
    To start an external child process worker.
    """
    ARGS = parse_cmdline()
    if ARGS.wd:
        os.chdir(ARGS.wd)
        sys.path.insert(0, ARGS.wd)

    if ARGS.testplan:
        sys.path.append(ARGS.testplan)
    if ARGS.testplan_deps:
        sys.path.append(ARGS.testplan_deps)
    try:
        import dependencies
        # This will also import dependencies from $TESTPLAN_DEPENDENCIES_PATH
    except ImportError:
        pass

    import testplan
    if ARGS.testplan_deps:
        os.environ[testplan.TESTPLAN_DEPENDENCIES_PATH] = ARGS.testplan_deps

    # After parsing cmdline arguments and adding testplan and its dependecies
    # to the sys.path, the main child process logic can be executed.
    from testplan.runners.pools import child_logic
    child_logic.main(ARGS)

