"""TODO."""

import os
import re
import sys
import json
import platform

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


def test_app_cmd():
    app = App(name='App', binary='binary')
    assert app.cmd == ['binary']
    app = App(name='App', pre_args=['a', 'b'], binary='binary')
    assert app.cmd == ['a', 'b', 'binary']
    app = App(name='App', args=['c', 'd'], binary='binary')
    assert app.cmd == ['binary', 'c', 'd']
    app = App(name='App',
                pre_args=['a', 'b'], args=['c', 'd'], binary='binary')
    assert app.cmd == ['a', 'b', 'binary', 'c', 'd']


def test_app_env():
    app = App(name='App', binary='echo',
              args=['%KEY%' if platform.system() == 'Windows' else '$KEY'],
              env={'KEY': 'VALUE'}, shell=True)
    with app:
        app.proc.wait()
    with open(app.std.out_path, 'r') as fobj:
        assert fobj.read().startswith('VALUE')


def run_app(cwd):
    app = App(name='App', binary='echo',
              args=['%cd%' if platform.system() == 'Windows' else '`pwd`'],
              shell=True, working_dir=cwd)
    with app:
        app.proc.wait()
    return app


def test_app_cwd():
    """Test working_dir usage."""
    import tempfile
    tempdir = tempfile.gettempdir()

    # Cwd set to custom dir
    app = run_app(cwd=tempdir)
    with open(app.std.out_path, 'r') as fobj:
        assert tempdir in fobj.read()

    # Cwd not set
    app = run_app(cwd=None)
    with open(app.std.out_path, 'r') as fobj:
        assert app.runpath in fobj.read()


def test_app_logfile():
    app_dir = 'AppDir'
    logfile = 'file.log'
    app = App(name='App', binary='echo',
              args=['hello', '>', os.path.join('AppDir', logfile)],
              app_dir_name=app_dir, logfile=logfile,
              shell=True)
    with app:
        app.proc.wait()
    assert os.path.exists(app.logpath) is True

    with open(app.logpath, 'r') as fobj:
        assert fobj.read().startswith('hello')


def test_extract_from_logfile():
    logfile = 'file.log'
    a = '1'
    b = '23a'
    message = 'Value a={a} b={b}'.format(a=a, b=b)
    log_regexps = [re.compile(r'.*a=(?P<a>[a-zA-Z0-9]*) .*'),
                   re.compile(r'.*b=(?P<b>[a-zA-Z0-9]*).*')]

    app = CustomApp(name='App', binary='echo',
                    args=[message, '>', logfile],
                    logfile=logfile,
                    log_regexps=log_regexps, shell=True)
    with app:
        assert app.extracts['a'] == a
        assert app.extracts['b'] == b


def test_extract_from_logfile_with_appdir():
    app_dir = 'AppDir'
    logfile = 'file.log'
    a = '1'
    b = '23a'
    message = 'Value a={a} b={b}'.format(a=a, b=b)
    log_regexps = [re.compile(r'.*a=(?P<a>[a-zA-Z0-9]*) .*'),
                   re.compile(r'.*b=(?P<b>[a-zA-Z0-9]*).*')]

    app = CustomApp(name='App', binary='echo',
                    args=[message, '>', os.path.join('AppDir', logfile)],
                    app_dir_name=app_dir, logfile=logfile,
                    log_regexps=log_regexps, shell=True)
    with app:
        assert app.extracts['a'] == a
        assert app.extracts['b'] == b


def test_binary_copy():
    binary = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                          'example_binary.py')
    log_regexps = [re.compile(r'.*Binary started.*'),
                   re.compile(r'.*Binary=(?P<value>[a-zA-Z0-9]*).*')]

    params = dict(name='App', binary=binary, log_regexps=log_regexps,
                  pre_args=[sys.executable], binary_copy=True)

    app = CustomApp(path_cleanup=True, **params)
    with app:
        # Will terminate the binary.
        assert app.extracts['value'] == 'started'

    app = CustomApp(path_cleanup=False, **params)
    with app:
        assert app.extracts['value'] == 'started'


def test_install_files():
    binary = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                          'example_binary.py')
    config = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                          'config.yaml')
    log_regexps = [re.compile(r'.*binary=(?P<binary>.*)'),
                   re.compile(r'.*command=(?P<command>.*)'),
                   re.compile(r'.*app_path=(?P<app_path>.*)')]
    app = CustomApp(name='App', binary=binary, pre_args=[sys.executable],
                    install_files=[config], log_regexps=log_regexps,
                    shell=True)
    with app:
        assert os.path.exists(app.extracts['binary'])
        assert bool(json.loads(app.extracts['command']))
        assert os.path.exists(app.extracts['app_path'])


def test_echo_hello():
    app = ProcWaitApp(name='App', binary='echo', args=['hello'],
                      app_dir_name='App', shell=True)
    assert app.cmd == ['echo', 'hello']
    with app:
        assert app.status.tag == app.status.STARTED
        assert app.cfg.app_dir_name in os.listdir(app.runpath)
    assert app.status.tag == app.status.STOPPED
    assert app.retcode == 0

    with open(app.std.out_path, 'r') as fobj:
        assert fobj.read().startswith('hello')
