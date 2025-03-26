#!/usr/bin/env python

import sys
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.common.utils.callable import pre, post

from testplan import test_plan
from testplan.report.testing.styles import Style


def pre_fn(_self, _env, result):
    result.log("pre_fn")


def post_fn(_self, _env, result):
    result.log("post_fn")


def after_start_hook(_, result):
    result.log("param ``env`` not used here")


@testsuite
class SimpleTest:
    def setup(self, _env, result):
        result.log("setup")

    def teardown(self, _env, result):
        result.log("tear down")

    def pre_testcase(self, name, _env, result, kwargs):
        result.log(f"name = {name}", description="pre_testcase")
        if kwargs:
            result.dict.log(kwargs, description="kwargs")

    def post_testcase(self, name, _env, result, kwargs):
        result.log(f"name = {name}", description="post_testcase")
        if kwargs:
            result.dict.log(kwargs, description="kwargs")

    @pre(pre_fn)
    @post(post_fn)
    @testcase
    def add_simple(self, _env, result):
        result.equal(10 + 5, 15)

    @testcase(
        parameters=((3, 3, 6), (7, 8, 15)),
        custom_wrappers=[pre(pre_fn), post(post_fn)],
    )
    def add_param(self, _env, result, a, b, expect, hoho=None):
        result.equal(a + b, expect)


@test_plan(
    name="Hooks",
    stdout_style=Style("assertion-detail", "assertion-detail"),
)
def main(plan):
    plan.add(
        MultiTest(
            name="Hooks",
            suites=[SimpleTest()],
            after_start=after_start_hook,
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
