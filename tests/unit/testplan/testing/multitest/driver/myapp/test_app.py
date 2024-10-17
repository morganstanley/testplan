"""Units test for the App driver."""

import json
import os
import platform
import re
import sys
import tempfile
import time
from functools import reduce
from itertools import count
from pathlib import Path

import psutil
import pytest

from testplan.common.entity import ActionResult
from testplan.testing.multitest.driver.app import App

from pytest_test_filters import skip_on_windows


MYAPP_DIR = os.path.dirname(__file__)


class ProcTerminateApp(App):
    def started_check(self) -> ActionResult:
        return self.proc.poll() is not None


def test_app_unexpected_retcode(runpath):
    app = ProcTerminateApp(
        name="App",
        binary=sys.executable,
        args=["-c", "import sys; sys.exit(0)"],
        expected_retcode=1,
        runpath=runpath,
    )
    with pytest.raises(RuntimeError):
        with app:
            pass


def test_app_cmd(runpath):
    """Test the app command is constructed correctly."""
    app = App(name="App", binary="binary", runpath=runpath)
    assert app.cmd == ["binary"]
    app = App(
        name="App", pre_args=["a", "b"], binary="binary", runpath=runpath
    )
    assert app.cmd == ["a", "b", "binary"]
    app = App(name="App", args=["c", "d"], binary="binary", runpath=runpath)
    assert app.cmd == ["binary", "c", "d"]
    app = App(
        name="App",
        pre_args=["a", "b"],
        args=["c", "d"],
        binary="binary",
        runpath=runpath,
    )
    assert app.cmd == ["a", "b", "binary", "c", "d"]


def test_app_env(runpath):
    """Test that environment variables are correctly passed down."""
    app = ProcTerminateApp(
        name="App",
        binary="echo",
        args=["%KEY%" if platform.system() == "Windows" else "$KEY"],
        env={"KEY": "VALUE"},
        shell=True,
        runpath=runpath,
    )
    with app:
        pass
    with open(app.std.out_path, "r") as fobj:
        assert fobj.read().startswith("VALUE")


def test_app_os_environ(runpath):
    """Test that os.environ is passed down."""
    os.environ["KEY"] = "VALUE"

    app = ProcTerminateApp(
        name="App",
        binary="echo",
        args=["%KEY%" if platform.system() == "Windows" else "$KEY"],
        shell=True,
        runpath=runpath,
    )
    with app:
        pass
    with open(app.std.out_path, "r") as fobj:
        assert fobj.read().startswith("VALUE")

    del os.environ["KEY"]


def test_app_fail_fast_with_log_regex(runpath):
    """Test that app fail fast instead of waiting for logs when app shutdown."""
    app = App(
        name="myapp",
        binary="echo",
        args=["yes"],
        shell=True,
        stderr_regexps=[re.compile(r".*no*")],
        status_wait_timeout=2,
        runpath=runpath,
    )
    with pytest.raises(
        RuntimeError,
        match=r"App\[myapp\] has unexpectedly stopped with: 0",
    ):
        app.start()
        app.wait(app.STATUS.STARTED)

    app.stop()


def test_app_cwd(runpath):
    """Test working_dir usage."""
    tempdir = tempfile.gettempdir()

    # Cwd set to custom dir
    app = run_app(cwd=tempdir, runpath=runpath)
    with open(app.std.out_path, "r") as fobj:
        assert tempdir in fobj.read()

    # Cwd not set
    app = run_app(cwd=None, runpath=runpath)
    with open(app.std.out_path, "r") as fobj:
        assert app.runpath in fobj.read()


def test_app_logfile(runpath):
    """Test running an App that writes to a logfile."""
    app_dir = "AppDir"
    logname = "file.log"
    app = ProcTerminateApp(
        name="App",
        binary="echo",
        args=["hello", ">", os.path.join("AppDir", logname)],
        app_dir_name=app_dir,
        logname=logname,
        shell=True,
        runpath=runpath,
    )
    with app:
        pass
    assert os.path.exists(app.logpath) is True

    with open(app.logpath, "r") as fobj:
        assert fobj.read().startswith("hello")


def test_extract_from_logfile(runpath):
    """Test extracting values from a logfile via regex matching."""
    logname = "file.log"
    a = "1"
    b = "23a"
    message = "Value a={a} b={b}".format(a=a, b=b)
    log_regexps = [
        re.compile(r".*a=(?P<a>[a-zA-Z0-9]*) .*"),
        re.compile(r".*b=(?P<b>[a-zA-Z0-9]*).*"),
    ]

    app = App(
        name="App",
        binary="echo",
        args=[message, ">", logname],
        logname=logname,
        log_regexps=log_regexps,
        shell=True,
        runpath=runpath,
    )
    with app:
        assert app.extracts["a"] == a
        assert app.extracts["b"] == b


def test_extract_from_logfile_with_appdir(runpath):
    """Test extracting values from a logfile within an app sub-directory."""
    app_dir = "AppDir"
    logname = "file.log"
    a = "1"
    b = "23a"
    message = "Value a={a} b={b}".format(a=a, b=b)
    log_regexps = [
        re.compile(r".*a=(?P<a>[a-zA-Z0-9]*) .*"),
        re.compile(r".*b=(?P<b>[a-zA-Z0-9]*).*"),
    ]

    app = App(
        name="App",
        binary="echo",
        args=[message, ">", os.path.join("AppDir", logname)],
        app_dir_name=app_dir,
        logname=logname,
        log_regexps=log_regexps,
        shell=True,
        runpath=runpath,
    )
    with app:
        assert app.extracts["a"] == a
        assert app.extracts["b"] == b


@pytest.mark.parametrize("strategy", ["copy", "link", "noop"])
def test_binary_strategy(runpath, strategy):
    """Test copying the binary under the runpath."""
    binary = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "example_binary.py"
    )
    stdout_regexps = [
        re.compile(r".*Binary started.*"),
        re.compile(r".*Binary=(?P<value>[a-zA-Z0-9]*).*"),
    ]

    params = {
        "name": "App",
        "binary": binary,
        "stdout_regexps": stdout_regexps,
        "pre_args": [sys.executable],
        "binary_strategy": strategy,
        "runpath": runpath,
    }

    app = App(path_cleanup=True, **params)
    with app:
        assert app.extracts["value"] == "started"

        if strategy == "copy":
            assert app.binary == os.path.join(
                app.runpath, "bin", "example_binary.py"
            )
            assert not os.path.islink(app.binary)

        elif strategy == "link" and platform.system() != "Windows":
            assert app.binary == os.path.join(
                app.runpath, "bin", "example_binary.py"
            )
            assert os.path.islink(app.binary)

        else:
            assert app.binary == binary


def test_install_files(runpath):
    """Test installing config files."""
    binary = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "example_binary.py"
    )
    config = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "config.yaml"
    )
    bfile = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "binary_file"
    )
    stdout_regexps = [
        re.compile(r".*binary=(?P<binary>.*)"),
        re.compile(r".*command=(?P<command>.*)"),
        re.compile(r".*app_path=(?P<app_path>.*)"),
    ]
    dst = runpath
    app = App(
        name="App",
        binary=binary,
        pre_args=[sys.executable],
        install_files=[
            config,
            bfile,
            (config, os.path.join(dst, "config.yaml")),
            (config, os.path.join("rel_path", "config.yaml")),
        ],
        stdout_regexps=stdout_regexps,
        shell=True,
        runpath=runpath,
    )
    with app:
        assert os.path.exists(app.extracts["binary"])
        assert bool(json.loads(app.extracts["command"]))
        assert os.path.exists(app.extracts["app_path"])
        assert os.path.exists(os.path.join(app.app_path, "etc", "binary_file"))
        assert os.path.exists(os.path.join(app.app_path, "etc", "config.yaml"))
        assert os.path.exists(os.path.join(dst, "config.yaml"))
        assert os.path.exists(
            os.path.join(app.app_path, "etc", "rel_path", "config.yaml")
        )


def test_echo_hello(runpath):
    """Test running a basic App that just echos Hello."""
    app = ProcTerminateApp(
        name="App",
        binary="echo",
        args=["hello"],
        app_dir_name="App",
        shell=True,
        runpath=runpath,
    )
    assert app.cmd == ["echo", "hello"]
    with app:
        assert app.status == app.status.STARTED
        assert app.cfg.app_dir_name in os.listdir(app.runpath)
    assert app.status == app.status.STOPPED
    assert app.retcode == 0

    with open(app.std.out_path, "r") as fobj:
        assert fobj.read().startswith("hello")


def test_stdin(runpath):
    """Test communicating with an App process' stdin."""
    app = App(
        name="Repeater",
        binary=sys.executable,
        args=[os.path.join(MYAPP_DIR, "repeater.py")],
        runpath=runpath,
    )
    with app:
        app.proc.communicate(input=b"Repeat me\nEOF")
        assert app.proc.poll() == 0

    with open(app.std.out_path) as f:
        stdout = f.read()
    assert stdout == "Repeat me\n"


def test_restart(runpath):
    """Test restart of an App"""
    app = App(
        name="Restarter",
        binary="echo",
        args=["Restarter app ran succesfully"],
        shell=True,
        runpath=runpath,
    )

    with app:
        app.restart()

        app_path = Path(app.app_path)
        app_dir_name = app_path.name

        # we have the moved app_path
        assert list(app_path.parent.glob(f"{app_dir_name}_*"))

        app.restart(clean=False)

        # we have the moved files in app_path
        assert list(app_path.glob("stdout_*"))
        assert list(app_path.glob("stderr_*"))


def run_app(cwd, runpath):
    """
    Utility function that runs an echo process and waits for it to terminate.
    """
    app = ProcTerminateApp(
        name="App",
        binary="echo",
        args=["%cd%" if platform.system() == "Windows" else "`pwd`"],
        shell=True,
        working_dir=cwd,
        runpath=runpath,
    )
    with app:
        pass
    return app


@skip_on_windows(reason='No need to dive into Windows "signals".')
@pytest.mark.parametrize(
    "app_args, force_stop, num_leftover",
    (
        ([], False, 0),
        (["--mask-sigterm", "parent"], False, 0),
        (["--mask-sigterm", "parent"], True, 0),
        (
            ["--mask-sigterm", "parent", "--sleep-time", "5"],
            False,
            1,
        ),
        (
            ["--mask-sigterm", "parent", "--sleep-time", "5"],
            True,
            0,
        ),
        (["--mask-sigterm", "child"], False, 2),
        (["--mask-sigterm", "child"], True, 0),
        (["--mask-sigterm", "all"], False, 3),
        (["--mask-sigterm", "all"], True, 0),
    ),
    ids=count(0),
)
def test_multiproc_app_stop(runpath, app_args, force_stop, num_leftover):
    """Test App driver stopping behaviour when used with a binary that create processes."""
    app = App(
        name="dummy_multi_proc",
        binary=sys.executable,
        args=["-u", os.path.join(MYAPP_DIR, "multi_proc_app.py"), *app_args],
        stdout_regexps=[
            re.compile(r"^parent pid (?P<pid>[0-9]+)$"),
            re.compile(r"^child 1 pid (?P<pid1>[0-9]+)$"),
            re.compile(r"^child 2 pid (?P<pid2>[0-9]+)$"),
        ],
        runpath=runpath,
        stop_timeout=1,
        async_start=False,
        expected_retcode=0,
    )
    app.start()
    try:
        app.stop()
    except Exception as e:
        if force_stop:
            app.force_stopped()
            # XXX: we don't wait on orphaned child procs, give OS some time
            time.sleep(0.01)
        else:
            assert "Timeout when stopping App" in str(
                e
            ) or "but actual return code" in str(e)

    procs = reduce(
        lambda x, y: psutil.pid_exists(y) and x + [psutil.Process(y)] or x,
        map(lambda x: int(app.extracts[x]), ["pid", "pid1", "pid2"]),
        [],
    )
    assert len(procs) == num_leftover
    for p in procs:
        p.kill()
        p.wait()
