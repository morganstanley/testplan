"""System process utilities module."""

import functools
import platform
import shlex
import subprocess
import threading
import time
import re
import warnings
from enum import Enum, auto
from signal import Signals
from typing import IO, Any, Callable, List, Union, Optional

import psutil

from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.common.utils.timing import (
    exponential_interval,
    get_sleeper,
    wait,
    TimeoutException,
)


def _log_proc(msg: Any, warn=False, output: IO = None):
    if output is not None:
        try:
            output.write("{}{}".format(msg, "\n"))
        except:
            pass
    if warn:
        warnings.warn(msg)


def process_is_alive(proc_id: int) -> bool:
    stat_file_path = f"/proc/{proc_id}/stat"
    try:
        with open(stat_file_path, "r") as stat_file:
            stat_content = stat_file.read()
        if re.match(r"\d+\s\(.*\)\s(\S+)\s.+", stat_content).group(1) != "Z":
            return False
        return True
    except:
        return True


def wait_process_clean(proc_id: int, timeout: int = 5, output: IO = None):
    if platform.system() != "Linux":
        return
    try:
        wait(lambda: process_is_alive(proc_id), timeout=timeout)
    except TimeoutException:
        _log_proc(
            msg=f"Process {proc_id} is not cleaned up",
            warn=True,
            output=output,
        )


def kill_process(
    proc: subprocess.Popen,
    timeout: int = 5,
    signal_: Optional[Signals] = None,
    output: Optional[IO] = None,
    on_failed_termination: Optional[Callable[[int, int], None]] = None,
) -> Union[int, None]:
    """
    If alive, kills the process.
    First call ``terminate()`` or pass ``signal_`` if specified
    to terminate for up to time specified in timeout parameter.
    If process hangs then call ``kill()``.

    :param proc: process to kill
    :param timeout: timeout in seconds, defaults to 5 seconds
    :param output: Optional file like object for writing logs.
    :param on_failed_termination : ``callable`` or ``None``
        A callback function that is executed when process fails
        to terminate after the `timeout`. When supplied, this callback
        will be executed after SIGTERM fails and before SIGKILL.
        It receives two arguments: pid as `int` and timeout as `int` and
        can be leveraged to collect additional diagnostic info about the process.
    :return: Exit code of process
    """
    _log = functools.partial(_log_proc, output=output)

    retcode = proc.poll()
    if retcode is not None:
        wait_process_clean(proc.pid, timeout=timeout)
        return retcode

    child_procs = psutil.Process(proc.pid).children(recursive=True)

    if signal_ is not None:
        proc.send_signal(signal_)
    else:
        proc.terminate()

    if timeout == 0:
        return retcode

    sleeper = get_sleeper((0.05, 1), timeout=timeout)
    while next(sleeper):
        if retcode is None:
            retcode = proc.poll()
        else:
            break

    if retcode is None:
        try:
            if on_failed_termination is not None:
                on_failed_termination(proc.pid, timeout)

            _log(msg="Binary still alive, killing it")
            proc.kill()
            proc.wait()
            wait_process_clean(proc.pid, timeout=timeout)
        except (RuntimeError, OSError, TimeoutException) as error:
            _log(msg="Could not kill process - {}".format(error), warn=True)

    def _log_child_exc(exc):
        _log(msg="While killing child process - {}".format(exc), warn=True)

    cleanup_child_procs(child_procs, timeout, _log_child_exc)
    return proc.returncode


def kill_process_psutil(
    proc: psutil.Process,
    timeout: int = 5,
    signal_: Optional[Signals] = None,
    output: Optional[IO] = None,
    on_failed_termination: Optional[Callable[[int, int], None]] = None,
) -> List[psutil.Process]:
    """
    If alive, kills the process (an instance of ``psutil.Process``).
    Try killing the child process at first and then killing itself.
    First call ``terminate()`` or pass ``signal_`` if specified
    to terminate for up to time specified in timeout parameter.
    If process hangs then call ``kill()``.

    :param proc: process to kill
    :param timeout: timeout in seconds, defaults to 5 seconds
    :param output: Optional file like object for writing logs.
    :param on_failed_termination : ``callable`` or ``None``
        A callback function that is executed when process fails
        to terminate after the `timeout`. When supplied, this callback
        will be executed after SIGTERM fails and before SIGKILL.
        It receives two arguments: pid as `int` and timeout as `int` and
        can be leveraged to collect additional diagnostic info about the process.
    :return: List of processes which are still alive
    """
    _log = functools.partial(_log_proc, output=output)
    try:
        # XXX: do we need to distinguish between parent and child?
        # XXX: here we basically apply on_failed_termination to all procs
        all_procs = proc.children(recursive=True) + [proc]
    except psutil.NoSuchProcess:
        return []

    try:
        if signal_ is not None:
            proc.send_signal(signal_)
        else:
            proc.terminate()
    except psutil.NoSuchProcess:
        pass  # already dead
    except Exception as exc:
        _log(msg="While terminating process - {}".format(exc), warn=True)
    _, alive = psutil.wait_procs(all_procs, timeout=timeout)

    if len(alive) > 0:
        for p in alive:
            try:
                if on_failed_termination is not None:
                    on_failed_termination(proc.pid, timeout)
                p.kill()
            except psutil.NoSuchProcess:
                pass  # already dead
            except Exception as exc:
                _log(msg="Could not kill process - {}".format(exc), warn=True)
        _, alive = psutil.wait_procs(alive, timeout=timeout)

    return alive


def kill_proc_and_child_procs(
    proc: subprocess.Popen,
    child_procs: List[psutil.Process],
    log: Callable[[BaseException], None] = None,
    timeout: int = 5,
) -> None:
    """
    Kill a process and its child processes.

    This function attempts to kill a given process and its child processes.
    It first kills the main process, waits for it to terminate, and then
    attempts to kill any remaining child processes.

    :param proc: The main process to kill.
    :type proc: subprocess.Popen
    :param child_procs: A list of child processes to kill.
    :type child_procs: List[psutil.Process]
    :param log: A callable to log exceptions, defaults to None.
    :type log: Callable[[BaseException], None], optional
    :param timeout: The timeout in seconds to wait for processes to terminate, defaults to 5.
    :type timeout: int, optional
    :return: The return code of the main process if it was terminated, otherwise None.
    :rtype: Union[int, None]
    """

    if proc is not None and proc.poll() is None:
        try:
            proc.kill()
            proc.wait()
            wait_process_clean(proc.pid, timeout=timeout)
        except Exception as exc:
            if log:
                log(exc)

    if child_procs:
        # we did not send sig term to child processes
        # thus no point to wait for them to terminate
        _, alive = psutil.wait_procs(child_procs, timeout=0)
        for p in alive:
            try:
                p.kill()
                p.wait()
            except psutil.NoSuchProcess:
                pass  # already reaped
            except Exception as exc:
                if log:
                    log(exc)


def cleanup_child_procs(
    procs: List[psutil.Process],
    timeout: float,
    log: Callable[[BaseException], None],
) -> None:
    """
    Kill child processes to eliminate possibly orphaned processes.

    :param procs: List of child processes to kill.
    :param timeout: Timeout in seconds, defaults to 5 seconds.
    :param log: Callback function to log exceptions.
    """
    _, alive = psutil.wait_procs(procs, timeout=timeout)
    for p in alive:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass  # already reaped
        except Exception as exc:
            log(exc)


DEFAULT_CLOSE_FDS = platform.system() != "Windows"


def subprocess_popen(
    args,
    bufsize=0,  # unbuffered (`io.DEFAULT_BUFFER_SIZE` for Python 3 by default)
    executable=None,
    stdin=None,
    stdout=None,
    stderr=None,
    preexec_fn=None,
    close_fds=DEFAULT_CLOSE_FDS,
    shell=False,
    cwd=None,
    env=None,
    universal_newlines=False,
    startupinfo=None,
    creationflags=0,
):
    """
    Wrapper for Subprocess.Popen, which defaults close_fds=True on Linux.
    It's the behaviour we nearly always want,
    and which has become default in 3.2+.

    On Windows, closed_fds=False.
    """
    if isinstance(args, list):
        for idx, arg in enumerate(args):
            args[idx] = str(arg)

    try:
        handle = subprocess.Popen(
            args,
            bufsize=bufsize,
            executable=executable,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            preexec_fn=preexec_fn,
            close_fds=close_fds,
            shell=shell,
            cwd=cwd,
            env=env,
            universal_newlines=universal_newlines,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        return handle
    except:
        print("subprocess.Popen failed, args: `{}`".format(args))
        raise


def _log_subprocess_output(logger, stdout, stderr):
    if stdout:
        logger.debug("Stdout:\n%s", stdout)
    if stderr:
        logger.debug("Stderr:\n%s", stderr)


class LogDetailsOption(Enum):
    LOG_ALWAYS = auto()
    LOG_ON_ERROR = auto()
    NEVER_LOG = auto()


def execute_cmd(
    cmd,
    label=None,
    check=True,
    stdout=None,
    stderr=None,
    logger=None,
    env=None,
    detailed_log: LogDetailsOption = LogDetailsOption.LOG_ON_ERROR,
):
    """
    Execute a subprocess command.

    :param cmd: Command to execute - list of parameters.
    :param label: Optional label for debugging
    :param check: When True, check that the return code of the command is 0 to
            ensure success - raises a RuntimeError otherwise. Defaults to
            True - should be explicitly disabled for commands that may
            legitimately return non-zero return codes.
    :param stdout: Optional file-like object to redirect stdout to.
    :param stderr: Optional file-like object to redirect stderr to.
    :param logger: Optional logger object as logging destination.
    :param env: Optional dict object as environment variables.
    :param detailed_log: Enum to determine when stdout and stderr outputs should
           be logged.
           LOG_ALWAYS - Outputs are logged on success and failure.
           LOG_ON_ERROR - Outputs are logged on failure.
           NEVER_LOG - Outputs are never logged.
    :return: Return code of the command.
    """
    if not logger:
        logger = TESTPLAN_LOGGER

    if isinstance(cmd, list):
        cmd = [str(a) for a in cmd]
        # for logging, easy to copy and execute
        cmd_string = shlex.join(cmd)
    else:
        cmd_string = cmd

    if not label:
        label = hash(cmd_string) % 1000

    if stdout is None:
        stdout = subprocess.PIPE

    if stderr is None:
        stderr = subprocess.PIPE

    logger.info("Executing command [%s]: '%s'", label, cmd_string)
    start_time = time.time()

    handler = subprocess.Popen(
        cmd, stdout=stdout, stderr=stderr, env=env, text=True, bufsize=0
    )
    output, error = handler.communicate()
    elapsed = time.time() - start_time

    if handler.returncode != 0:
        logger.warning(
            "Failed executing command [%s] after %.2f sec.", label, elapsed
        )
        if detailed_log is not LogDetailsOption.NEVER_LOG:
            _log_subprocess_output(logger, output, error)
        if check:
            raise RuntimeError(
                "Command '{}' returned with non-zero exit code {}".format(
                    cmd_string, handler.returncode
                )
            )
    else:
        logger.debug("Command [%s] finished in %.2f sec", label, elapsed)
        if detailed_log is LogDetailsOption.LOG_ALWAYS:
            _log_subprocess_output(logger, output, error)

    return handler.returncode


def execute_cmd_2(
    cmd,
    label=None,
    check=True,
    stdout=None,
    stderr=None,
    logger=None,
    env=None,
    detailed_log: LogDetailsOption = LogDetailsOption.LOG_ON_ERROR,
):
    """
    Execute a subprocess command.

    :param cmd: Command to execute - list of parameters.
    :param label: Optional label for debugging
    :param check: When True, check that the return code of the command is 0 to
            ensure success - raises a RuntimeError otherwise. Defaults to
            True - should be explicitly disabled for commands that may
            legitimately return non-zero return codes.
    :param stdout: Optional file-like object to redirect stdout to.
    :param stderr: Optional file-like object to redirect stderr to.
    :param logger: Optional logger object as logging destination.
    :param env: Optional dict object as environment variables.
    :param detailed_log: Enum to determine when stdout and stderr outputs should
           be logged.
           LOG_ALWAYS - Outputs are logged on success and failure.
           LOG_ON_ERROR - Outputs are logged on failure.
           NEVER_LOG - Outputs are never logged.
    :return: Return code of the command.
    """
    if not logger:
        logger = TESTPLAN_LOGGER

    if isinstance(cmd, list):
        cmd = [str(a) for a in cmd]
        # for logging, easy to copy and execute
        cmd_string = shlex.join(cmd)
    else:
        cmd_string = cmd

    if not label:
        label = str(hash(cmd_string) % 1000)

    if stdout is None:
        stdout = subprocess.PIPE

    if stderr is None:
        stderr = subprocess.PIPE

    logger.info("Executing command [%s]: '%s'", label, cmd_string)
    start_time = time.time()

    handler = subprocess.Popen(
        cmd, stdout=stdout, stderr=stderr, env=env, text=True, bufsize=0
    )
    output, error = handler.communicate()
    elapsed = time.time() - start_time

    if handler.returncode != 0:
        logger.warning(
            "Failed executing command [%s] after %.2f sec.", label, elapsed
        )
        if detailed_log is not LogDetailsOption.NEVER_LOG:
            _log_subprocess_output(logger, output, error)
        if check:
            raise RuntimeError(
                f"Command '{cmd_string}' returned with non-zero exit code {handler.returncode},\n"
                f"stdout: {stdout}\n"
                f"stderr: {stderr}\n"
            )
    else:
        logger.debug("Command [%s] finished in %.2f sec", label, elapsed)
        if detailed_log is LogDetailsOption.LOG_ALWAYS:
            _log_subprocess_output(logger, output, error)

    return handler.returncode, output, error


def enforce_timeout(process, timeout=1, callback=None, output=None):
    _log = functools.partial(_log_proc, output=output)

    def _inner():
        begin = time.time()
        intervals = exponential_interval(maximum=10)

        while True:
            if process.returncode is not None:
                _log(msg="Process returncode: {}".format(process.returncode))
                break
            elif time.time() - begin >= timeout:
                _log(
                    msg="Killing binary after"
                    " reaching timeout value {}s".format(timeout)
                )

                try:
                    if callback:
                        callback()

                finally:
                    kill_process(process, output=output)
                break
            else:
                delay = next(intervals)
                _log(msg="Sleeping for {}".format(delay))
                time.sleep(delay)
        _log("Exiting loop")

    timeout_checker = threading.Thread(target=_inner)
    timeout_checker.daemon = True
    timeout_checker.start()

    return timeout_checker
