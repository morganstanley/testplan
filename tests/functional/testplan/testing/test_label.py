from testplan import TestplanMock
from testplan.testing.multitest import MultiTest, testsuite, testcase


@testsuite
class AlphaSuite:
    @testcase
    def test_pass(self, env, result):
        result.true(True)


def test_label():
    mockplan = TestplanMock(name="test_label", label="my_label")

    multitest = MultiTest(
        name="MyMultitest",
        suites=[AlphaSuite()],
    )
    mockplan.add(multitest)
    mockplan.run()

    assert mockplan.report.label == "my_label"
