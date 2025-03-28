from time import sleep

import pytest

import testplan.testing.multitest as mt
from testplan.common.utils.selector import Eq
from testplan.common.report import Status
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

    assert MT_NAME in r.results
    repo = r.results[MT_NAME].report
    assert len(repo) == 1
    assert len(repo.entries[0]) == 1
    # Check if the multitest has the testcase entry
    assert repo.entries[0].entries[0].name == "case_a"
    # Check if the testcase has assertion
    assert len(repo.entries[0].entries[0].entries) == 1
    assert r._discard_pending is True

    if has_result:
        assert repo.entries[0].status == Status.FAILED
    else:
        assert repo.entries[0].status == Status.INCOMPLETE
