"""System process utilities module."""

import time
import signal
import psutil
import warnings

import subprocess
import platform
import threading
import functools

from .timing import exponential_interval
from testplan.common.utils.logger import TESTPLAN_LOGGER


def _log_proc(msg, warn=False, output=None):
    if output is not None:
        try:
            output.write('{}{}'.format(msg, '\n'))
        except:
            pass
    if warn:
        warnings.warn(msg)


def kill_process(proc, timeout=5, signal_=None, output=None):
    """
    If alive, kills the process.
    First call ``terminate()`` or pass ``signal_`` if specified
    to terminate for up to time specified in timeout parameter.

    If process hangs then call ``kill()``.

    :param proc: process to kill
    :type proc: ``subprocess.Popen``
    :param timeout: timeout in seconds, defaults to 5 seconds
    :type timeout: ``int``
    :param output: Optional file like object for writing logs.
    :type output: ``file``
    """
    _log = functools.partial(_log_proc, output=output)

    retcode = proc.poll()

    if retcode is not None:
        return retcode

    parent = psutil.Process(proc.pid)
    for child in parent.children(recursive=True):
        try:
            child.send_signal(signal.SIGTERM)
        except Exception as exc:
            _log(
                msg='While terminating child proc - {}'.format(exc),
                warn=True
            )

    if signal_ is not None:
        proc.send_signal(signal_)
    else:
        proc.terminate()

    begin = time.time()
    intervals = exponential_interval(initial=0.05, multiplier=1.1, maximum=1)

    while time.time() - begin >= timeout and retcode is None:
        retcode = proc.poll()

        if retcode is None:
            time.sleep(next(intervals))

    if retcode is None:
        try:
            _log(msg='Binary still alive, killing it')
            proc.kill()
            proc.wait()
        except (RuntimeError, OSError) as error:
            _log(
                msg='Could not kill process - {}'.format(error),
                warn=True
            )

    return proc.returncode


DEFAULT_CLOSE_FDS = platform.system() != 'Windows'


def subprocess_popen(
        args, bufsize=0, executable=None, stdin=None,
        stdout=None, stderr=None, preexec_fn=None,
        close_fds=DEFAULT_CLOSE_FDS, shell=False, cwd=None,
        env=None, universal_newlines=False,
        startupinfo=None, creationflags=0
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
            args, bufsize=bufsize, executable=executable, stdin=stdin,
            stdout=stdout, stderr=stderr, preexec_fn=preexec_fn,
            close_fds=close_fds, shell=shell, cwd=cwd,
            env=env, universal_newlines=universal_newlines,
            startupinfo=startupinfo, creationflags=creationflags
        )
        return handle
    except:
        print('subprocess.Popen failed, args: `{}`'.format(args))
        raise


def execute_cmd(
        cmd, label=None, check=True, stdout=None, stderr=None, logger=None):
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
    :return: Return code of the command.
    """
    if not logger:
        logger = TESTPLAN_LOGGER

    if isinstance(cmd, list):
        cmd = [str(a) for a in cmd]
        cmd_string = ' '.join(cmd)  # for logging, easy to copy and execute
    else:
        cmd_string = cmd

    if not label:
        label = hash(cmd_string) % 1000

    read_stdout = False
    if stdout is None:
        stdout = subprocess.PIPE
        read_stdout = True

    read_stderr = False
    if stderr is None:
        stderr = subprocess.PIPE
        read_stderr = True

    logger.debug("Executing command [{}]: '{}'".format(label, cmd_string))
    start_time = time.time()

    handler = subprocess.Popen(
        cmd,
        stdout=stdout,
        stderr=stderr,
        stdin=subprocess.PIPE)
    handler.stdin.write(bytes('y\n'.encode('utf-8')))
    handler.wait()
    elapsed = time.time()-start_time

    if handler.returncode != 0:
        logger.debug('Failed executing command [{}] after {} sec.'.format(
                label, elapsed))

        if read_stdout:
            out = handler.stdout.read()
            logger.debug('Stdout:\n{}'.format(out))

        if read_stderr:
            err = handler.stderr.read()
            logger.debug('Stderr:\n{}'.format(err))

        if check:
            raise RuntimeError(
                "Command '{}' returned with non-zero exit code {}"
                .format(cmd_string, handler.returncode))
    else:
        logger.debug('Command [{}] finished in {} sec'.format(
            label, elapsed
        ))

    return handler.returncode


def enforce_timeout(process, timeout=1, callback=None, output=None):
    _log = functools.partial(_log_proc, output=output)

    def _inner():
        begin = time.time()
        intervals = exponential_interval(maximum=10)

        while True:
            if process.returncode is not None:
                _log(msg='Process returncode: {}'.format(process.returncode))
                break
            elif time.time() - begin >= timeout:
                _log(msg='Killing binary after'
                         ' reaching timeout value {}s'.format(timeout))

                try:
                    if callback:
                        callback()

                finally:
                    kill_process(process, output=output)
                break
            else:
                delay = next(intervals)
                _log(msg='Sleeping for {}'.format(delay))
                time.sleep(delay)
        _log('Exiting loop')

    timeout_checker = threading.Thread(target=_inner)
    timeout_checker.daemon = True
    timeout_checker.start()
