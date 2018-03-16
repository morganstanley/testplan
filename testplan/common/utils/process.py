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
    for child in parent.children():
        try:
            child.send_signal(signal.SIGTERM)
        except Exception as exc:
            _log (
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
        except OSError as error:
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


def enforce_timeout(process, timeout=1, callback=None, output=None):
    _log= functools.partial(_log_proc, output=output)

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

                kill_process(process, output=output)

                if callback:
                    callback()
                break
            else:
                delay = next(intervals)
                _log(msg='Sleeping for {}'.format(delay))
                time.sleep(delay)
        _log('Exiting loop')

    timeout_checker = threading.Thread(target=_inner)
    timeout_checker.daemon = True
    timeout_checker.start()
