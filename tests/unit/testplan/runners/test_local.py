from time import sleep

import pytest

import testplan.testing.multitest as mt
from testplan.common.utils.selector import Eq
from testplan.runnable import TestRunner
from testplan.runners.local import LocalRunner


@mt.testsuite
class Suite:
    def __init__(self, pre_sleep, post_sleep):
        self.pre = pre_sleep
        self.post = post_sleep

    @mt.testcase
    def case_a(self, env, result):
        sleep(self.pre)
        result.true(False)
        sleep(self.post)


MT_NAME = "dummy_mt"


def gen_mt(*suites):
    return mt.MultiTest(MT_NAME, suites=suites)


@pytest.mark.parametrize(
    "pre_sleep,post_sleep,out_sleep,has_result",
    (
        (1, 0, 0.5, False),
        (0, 1, 0.5, False),
        (0, 0, 0.5, True),
    ),
)
def test_local_discard_pending(pre_sleep, post_sleep, out_sleep, has_result):
    par = TestRunner(name="in-the-middle-of-unit-tests")
    par.add_resource(LocalRunner("non-express"))
    mt = gen_mt(Suite(pre_sleep, post_sleep))
    par.add(mt, "non-express")
    r: LocalRunner = par.resources["non-express"]
    r.start()
    sleep(out_sleep)
    par.discard_pending_tasks(Eq("non-express"))
    r.stop()
    if has_result:
        # we don't have other runners here, casted messages might not get
        # processed in time before runner dies
        assert MT_NAME in r.results
        repo = r.results[MT_NAME].report
        assert len(repo) == 3
        assert len(repo.entries[1]) == 1
    else:
        assert r._discard_pending is True
        assert len(r.results) == 0
