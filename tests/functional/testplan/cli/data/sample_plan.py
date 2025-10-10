import os

from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style


@testsuite
class Suite:
    def __init__(self):
        if os.environ.get("ADD_HOOKS"):
            self.pre_testcase = lambda name, _env, result: result.log(
                f"name = {name}", description="pre_testcase"
            )
            self.post_testcase = lambda name, _env, result: result.log(
                f"name = {name}", description="post_testcase"
            )
            self.setup = lambda _env, result: result.log(f"TS setup")
            self.teardown = lambda _env, result: result.log("TS teardown")

    @testcase
    def passing(self, _env, result):
        result.equal(1, 1, description="passing assertion")

    @testcase
    def failing(self, _env, result):
        result.equal(
            {"a": 1, "b": 2}, {"b": 2}, description="failing assertion"
        )


@test_plan(
    name="SamplePlan",
    stdout_style=Style("assertion-detail", "assertion-detail"),
)
def main(plan):
    plan.add(MultiTest(name="MyMultiTest", suites=[Suite()]))


if __name__ == "__main__":
    main()
