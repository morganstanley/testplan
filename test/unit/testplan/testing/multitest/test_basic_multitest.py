"""TODO."""

import os

from testplan.common.utils.path import default_runpath
from testplan.testing.multitest import MultiTest
from testplan.testing.multitest.base import MultiTestConfig


def test_multitest_runpath():
    # # No runpath specified
    mtest = MultiTest(name='Mtest', suites=[])
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == default_runpath(mtest)
    assert mtest._runpath == default_runpath(mtest)

    # runpath in local cfg
    custom = '{sep}var{sep}tmp{sep}custom'.format(sep=os.sep)
    mtest = MultiTest(name='Mtest', suites=[], runpath=custom)
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == custom
    assert mtest._runpath == custom

    # runpath in global cfg
    global_runpath = '{sep}var{sep}tmp{sep}global_level'.format(sep=os.sep)
    par = MultiTestConfig(name='Mtest', suites=[], runpath=global_runpath)
    mtest = MultiTest(name='Mtest', suites=[])
    mtest.cfg.parent = par
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == global_runpath
    assert mtest._runpath == global_runpath

    # runpath in global cfg and local
    global_runpath = '{sep}var{sep}tmp{sep}global_level'.format(sep=os.sep)
    local_runpath = '{sep}var{sep}tmp{sep}local_runpath'.format(sep=os.sep)
    par = MultiTestConfig(name='Mtest', suites=[], runpath=global_runpath)
    mtest = MultiTest(name='Mtest', suites=[], runpath=local_runpath)
    mtest.cfg.parent = par
    assert mtest.runpath is None
    assert mtest._runpath is None
    mtest.run()
    assert mtest.runpath == local_runpath
    assert mtest._runpath == local_runpath
