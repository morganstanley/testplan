"""
This module provides helper functions that will add common information of
Testplan execution to test report.

They could be used directly in testcases or provided to
pre/pose_start/stop hooks.

Also provided is a predefined testsuite that can be included in user's
Multitest directly.
"""

__all__ = [
    "DriverLogCollector",
    "get_hardware_info",
    "log_pwd",
    "log_hardware",
    "log_cmd",
    "log_environment",
    "attach_log",
    "attach_driver_logs_if_failed",
    "extract_driver_metadata",
    "clean_runpath_if_passed",
    "TestplanExecutionInfo",
]

import logging
import os
import psutil
import shutil
import socket
import sys
from typing import Dict, List

from testplan.common.entity import Environment
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.common.utils.path import pwd
from testplan.testing.multitest import testsuite, testcase
from testplan.testing.multitest.result import Result


class DriverLogCollector:

    """
    Customizable file collector class used for collecting driver logs.

    :param name: Name of the object shown in the report.
    :param description: Text description for the assertion.
    :param ignore: List of patterns of file name to ignore when
        attaching a directory.
    :param file_pattern: List of patterns of file name to include when
        attaching a directory. (Defaults: "stdout*", "stderr*")
    :param recursive: Recursively traverse sub-directories and attach
        all files, default is to only attach files in top directory.
    :param failure_only: Only collect files on failure.
    """

    def __init__(
        self,
        name: str = "DriverLogCollector",
        description: str = "logs",
        ignore: List[str] = None,
        file_pattern: List[str] = None,
        recursive: bool = True,
        failure_only: bool = True,
    ) -> None:
        self.__name__ = name
        self.description = description
        self.ignore = ignore
        self.file_pattern = file_pattern or ["stdout*", "stderr*"]
        self.recursive = recursive
        self.failure_only = failure_only

    def __call__(
        self,
        env: Environment,
        result: Result,
    ) -> None:
        """
        Attaches log files to the report for each driver.
        """

        if not env.parent.report.passed or not self.failure_only:
            for driver in env:
                result.attach(
                    path=driver.runpath,
                    description=f"Driver: {driver.name} - {self.description}",
                    only=self.file_pattern,
                    recursive=self.recursive,
                    ignore=self.ignore,
                )


def get_hardware_info() -> Dict:
    """
    Return a variety of host hardware information.

    :return: dictionary of hardware information
    """
    data = {
        "CPU count": psutil.cpu_count(),
        "CPU frequence": str(psutil.cpu_freq()),
        "CPU percent": psutil.cpu_percent(interval=1, percpu=True),
        "Memory": str(psutil.virtual_memory()),
        "Swap": str(psutil.swap_memory()),
        "Disk usage": str(psutil.disk_usage(os.getcwd())),
        "Net interface addresses": psutil.net_if_addrs(),
        "PID": os.getpid(),
    }

    load_avg = ("N/A", "N/A", "N/A")
    try:
        load_avg = psutil.getloadavg()
    except Exception as exc:
        print(exc)

    data["Average load"] = dict(
        zip(["Over 1 min", "Over 5 min", "Over 15 min"], load_avg)
    )

    return data


def log_hardware(result: Result) -> None:
    """
    Saves host hardware information to the report.

    :param result: testcase result
    """
    result.log(socket.getfqdn(), description="Current Host")
    hardware = get_hardware_info()
    result.dict.log(hardware, description="Hardware info")


def log_environment(result: Result) -> None:
    """
    Saves host environment variable to the report.

    :param result: testcase result
    """
    result.dict.log(
        dict(os.environ), description="Current environment variable"
    )


def log_pwd(result: Result) -> None:
    """
    Saves current path to the report.

    :param result: testcase result
    """
    result.log(pwd(), description="PWD environment")
    result.log(os.getcwd(), description="Current real path")


def log_cmd(result: Result) -> None:
    """
    Saves command line arguments to the report.

    :param result: testcase result
    """
    result.log(sys.argv, description="Command")
    result.log(
        os.path.abspath(os.path.realpath(sys.argv[0])),
        description="Resolved path",
    )


def extract_driver_metadata(env: Environment, result: Result) -> None:
    """
    Saves metadata of each driver to the report.

    :param env: environment
    :param result: testcase result
    """
    data = {rss.name: rss.extract_driver_metadata().to_dict() for rss in env}
    result.dict.log(data, description="Environment metadata")


def attach_log(result: Result) -> None:
    """
    Attaches top-level testplan.log file to the report.

    :param result: testcase result
    """
    log_handlers = TESTPLAN_LOGGER.handlers
    for handler in log_handlers:
        if isinstance(handler, logging.FileHandler):
            result.attach(handler.baseFilename, description="Testplan log")
            return


def attach_driver_logs_if_failed(
    env: Environment,
    result: Result,
) -> None:
    """
    Attaches stdout and stderr files to the report for each driver.

    :param env: environment
    :param result: testcase result
    """
    stdout_logger = DriverLogCollector(
        file_pattern=["stdout*"], description="stdout"
    )
    stderr_logger = DriverLogCollector(
        file_pattern=["stderr*"], description="stderr"
    )

    stdout_logger(env, result)
    stderr_logger(env, result)


def clean_runpath_if_passed(
    env: Environment,
    result: Result,
) -> None:
    """
    Deletes multitest-level runpath if the multitest passed.

    :param env: environment
    :param result: result object
    """
    multitest = env.parent
    if multitest.report.passed:
        shutil.rmtree(multitest.runpath, ignore_errors=True)


@testsuite
class TestplanExecutionInfo:
    """
    Utility testsuite to log generic information of Testplan execution.
    """

    @testcase
    def environment(self, env, result):
        """
        Environment
        """
        log_environment(result)

    @testcase
    def path(self, env, result):
        """
        Execution path
        """
        log_pwd(result)
        log_cmd(result)

    @testcase
    def hardware(self, env, result):
        """
        Host hardware
        """
        log_hardware(result)

    @testcase
    def logging(self, env, result):
        """
        Testplan log
        """
        attach_log(result)
