"""UTs for the App driver."""

import os
import re
import sys
import json
import platform
import tempfile

from testplan.common.utils.timing import wait

from testplan.testing.multitest.driver.app import App


class CustomApp(App):
    def started_check(self, timeout=None):
        wait(lambda: self.extract_values(), 5, raise_on_timeout=False)


class ProcWaitApp(App):
    def started_check(self, timeout=None):
        self.proc.wait()

    def stopped_check(self, timeout=None):
        wait(lambda: self.proc is None, 10, raise_on_timeout=True)


def test_app_cmd(runpath):
    """Test the app command is constructed correctly."""
    app = App(name='App', binary='binary', runpath=runpath)
    assert app.cmd == ['binary']
    app = App(
        name='App', pre_args=['a', 'b'], binary='binary', runpath=runpath)
    assert app.cmd == ['a', 'b', 'binary']
    app = App(name='App', args=['c', 'd'], binary='binary', runpath=runpath)
    assert app.cmd == ['binary', 'c', 'd']
    app = App(name='App',
              pre_args=['a', 'b'],
              args=['c', 'd'],
              binary='binary',
              runpath=runpath)
    assert app.cmd == ['a', 'b', 'binary', 'c', 'd']


def test_app_env(runpath):
    """Test that environment variables are correctly passed down."""
    app = App(name='App',
              binary='echo',
              args=['%KEY%' if platform.system() == 'Windows' else '$KEY'],
              env={'KEY': 'VALUE'},
              shell=True,
              runpath=runpath)
    with app:
        app.proc.wait()
    with open(app.std.out_path, 'r') as fobj:
        assert fobj.read().startswith('VALUE')


def test_app_cwd(runpath):
    """Test working_dir usage."""
    tempdir = tempfile.gettempdir()

    # Cwd set to custom dir
    app = run_app(cwd=tempdir, runpath=runpath)
    with open(app.std.out_path, 'r') as fobj:
        assert tempdir in fobj.read()

    # Cwd not set
    app = run_app(cwd=None, runpath=runpath)
    with open(app.std.out_path, 'r') as fobj:
        assert app.runpath in fobj.read()


def test_app_logfile(runpath):
    """Test running an App that writes to a logfile."""
    app_dir = 'AppDir'
    logfile = 'file.log'
    app = App(name='App',
              binary='echo',
              args=['hello', '>', os.path.join('AppDir', logfile)],
              app_dir_name=app_dir,
              logfile=logfile,
              shell=True,
              runpath=runpath)
    with app:
        app.proc.wait()
    assert os.path.exists(app.logpath) is True

    with open(app.logpath, 'r') as fobj:
        assert fobj.read().startswith('hello')


def test_extract_from_logfile(runpath):
    """Test extracting values from a logfile via regex matching."""
    logfile = 'file.log'
    a = '1'
    b = '23a'
    message = 'Value a={a} b={b}'.format(a=a, b=b)
    log_regexps = [re.compile(r'.*a=(?P<a>[a-zA-Z0-9]*) .*'),
                   re.compile(r'.*b=(?P<b>[a-zA-Z0-9]*).*')]

    app = CustomApp(name='App',
                    binary='echo',
                    args=[message, '>', logfile],
                    logfile=logfile,
                    log_regexps=log_regexps,
                    shell=True,
                    runpath=runpath)
    with app:
        assert app.extracts['a'] == a
        assert app.extracts['b'] == b


def test_extract_from_logfile_with_appdir(runpath):
    """Test extracting values from a logfile within an app sub-directory."""
    app_dir = 'AppDir'
    logfile = 'file.log'
    a = '1'
    b = '23a'
    message = 'Value a={a} b={b}'.format(a=a, b=b)
    log_regexps = [re.compile(r'.*a=(?P<a>[a-zA-Z0-9]*) .*'),
                   re.compile(r'.*b=(?P<b>[a-zA-Z0-9]*).*')]

    app = CustomApp(name='App',
                    binary='echo',
                    args=[message, '>', os.path.join('AppDir', logfile)],
                    app_dir_name=app_dir,
                    logfile=logfile,
                    log_regexps=log_regexps,
                    shell=True,
                    runpath=runpath)
    with app:
        assert app.extracts['a'] == a
        assert app.extracts['b'] == b


def test_binary_copy(runpath):
    """Test copying the binary under the runpath."""
    binary = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                          'example_binary.py')
    log_regexps = [re.compile(r'.*Binary started.*'),
                   re.compile(r'.*Binary=(?P<value>[a-zA-Z0-9]*).*')]

    params = {
        'name': 'App',
        'binary': binary,
        'log_regexps': log_regexps,
        'pre_args': [sys.executable],
        'binary_copy': True,
        'runpath': runpath,
    }

    app = CustomApp(path_cleanup=True, **params)
    with app:
        # Will terminate the binary.
        assert app.extracts['value'] == 'started'

    app = CustomApp(path_cleanup=False, **params)
    with app:
        assert app.extracts['value'] == 'started'


def test_install_files(runpath):
    """Test installing config files."""
    binary = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                          'example_binary.py')
    config = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                          'config.yaml')
    log_regexps = [re.compile(r'.*binary=(?P<binary>.*)'),
                   re.compile(r'.*command=(?P<command>.*)'),
                   re.compile(r'.*app_path=(?P<app_path>.*)')]
    app = CustomApp(name='App',
                    binary=binary,
                    pre_args=[sys.executable],
                    install_files=[config],
                    log_regexps=log_regexps,
                    shell=True,
                    runpath=runpath)
    with app:
        assert os.path.exists(app.extracts['binary'])
        assert bool(json.loads(app.extracts['command']))
        assert os.path.exists(app.extracts['app_path'])


def test_echo_hello(runpath):
    """Test running a basic App that just echos Hello."""
    app = ProcWaitApp(name='App',
                      binary='echo',
                      args=['hello'],
                      app_dir_name='App',
                      shell=True,
                      runpath=runpath)
    assert app.cmd == ['echo', 'hello']
    with app:
        assert app.status.tag == app.status.STARTED
        assert app.cfg.app_dir_name in os.listdir(app.runpath)
    assert app.status.tag == app.status.STOPPED
    assert app.retcode == 0

    with open(app.std.out_path, 'r') as fobj:
        assert fobj.read().startswith('hello')


def run_app(cwd, runpath):
    """
    Utility function that runs an echo process and waits for it to terminate.
    """
    app = App(name='App',
              binary='echo',
              args=['%cd%' if platform.system() == 'Windows' else '`pwd`'],
              shell=True,
              working_dir=cwd,
              runpath=runpath)
    with app:
        app.proc.wait()
    return app

