import pytest

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import TestplanMock
from testplan.common.utils.testing import (
    argv_overridden,
    check_report_context,
)
from testplan.testing import ordering


@testsuite
class Alpha:
    @testcase
    def test_ccc(self, env, result):
        pass

    @testcase
    def test_bbb(self, env, result):
        pass

    @testcase
    def test_aaa(self, env, result):
        pass


@testsuite
class Beta:
    @testcase
    def test_ccc(self, env, result):
        pass

    @testcase
    def test_xxx(self, env, result):
        pass

    @testcase(parameters=[0, 1])
    def test_bbb(self, env, result, val):
        pass

    @testcase
    def test_aaa(self, env, result):
        pass

    @testcase(parameters=[3, 2, 1])
    def test_yyy(self, env, result, val):
        pass


@pytest.mark.parametrize(
    "sorter, report_ctx",
    (
        # Case 1, noop, original declaration & insertion order
        (
            ordering.NoopSorter(),
            [
                (
                    "Multitest",
                    [
                        (
                            "Beta",
                            [
                                "test_ccc",
                                "test_xxx",
                                (
                                    "test_bbb",
                                    ["test_bbb <val=0>", "test_bbb <val=1>"],
                                ),
                                "test_aaa",
                                (
                                    "test_yyy",
                                    [
                                        "test_yyy <val=3>",
                                        "test_yyy <val=2>",
                                        "test_yyy <val=1>",
                                    ],
                                ),
                            ],
                        ),
                        ("Alpha", ["test_ccc", "test_bbb", "test_aaa"]),
                    ],
                )
            ],
        ),
        # Case 2, alphanumerical
        (
            ordering.AlphanumericSorter(),
            [
                (
                    "Multitest",
                    [
                        ("Alpha", ["test_aaa", "test_bbb", "test_ccc"]),
                        (
                            "Beta",
                            [
                                "test_aaa",
                                (
                                    (
                                        "test_bbb",
                                        [
                                            "test_bbb <val=0>",
                                            "test_bbb <val=1>",
                                        ],
                                    )
                                ),
                                "test_ccc",
                                "test_xxx",
                                (
                                    "test_yyy",
                                    [
                                        "test_yyy <val=1>",
                                        "test_yyy <val=2>",
                                        "test_yyy <val=3>",
                                    ],
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
        # Case 3, shuffle all
        (
            ordering.ShuffleSorter(seed=7),
            [
                (
                    "Multitest",
                    [
                        (
                            "Beta",
                            [
                                (
                                    "test_yyy",
                                    [
                                        "test_yyy <val=1>",
                                        "test_yyy <val=3>",
                                        "test_yyy <val=2>",
                                    ],
                                ),
                                "test_ccc",
                                "test_aaa",
                                "test_xxx",
                                (
                                    "test_bbb",
                                    ["test_bbb <val=0>", "test_bbb <val=1>"],
                                ),
                            ],
                        ),
                        ("Alpha", ["test_aaa", "test_ccc", "test_bbb"]),
                    ],
                )
            ],
        ),
        # # Case 4, shuffle suites
        (
            ordering.ShuffleSorter(seed=7, shuffle_type="suites"),
            [
                (
                    "Multitest",
                    [
                        (
                            "Beta",
                            [
                                "test_ccc",
                                "test_xxx",
                                (
                                    "test_bbb",
                                    ["test_bbb <val=0>", "test_bbb <val=1>"],
                                ),
                                "test_aaa",
                                (
                                    "test_yyy",
                                    [
                                        "test_yyy <val=3>",
                                        "test_yyy <val=2>",
                                        "test_yyy <val=1>",
                                    ],
                                ),
                            ],
                        ),
                        ("Alpha", ["test_ccc", "test_bbb", "test_aaa"]),
                    ],
                )
            ],
        ),
        # # Case 5, shuffle testcases
        (
            ordering.ShuffleSorter(seed=7, shuffle_type="testcases"),
            [
                (
                    "Multitest",
                    [
                        (
                            "Beta",
                            [
                                (
                                    "test_yyy",
                                    [
                                        "test_yyy <val=1>",
                                        "test_yyy <val=3>",
                                        "test_yyy <val=2>",
                                    ],
                                ),
                                "test_ccc",
                                "test_aaa",
                                "test_xxx",
                                (
                                    "test_bbb",
                                    ["test_bbb <val=0>", "test_bbb <val=1>"],
                                ),
                            ],
                        ),
                        ("Alpha", ["test_aaa", "test_ccc", "test_bbb"]),
                    ],
                )
            ],
        ),
    ),
)
def test_programmatic_ordering(sorter, report_ctx):
    multitest = MultiTest(name="Multitest", suites=[Beta(), Alpha()])
    plan = TestplanMock(name="plan", test_sorter=sorter)
    plan.add(multitest)
    plan.run()

    test_report = plan.report
    check_report_context(test_report, report_ctx)


@pytest.mark.parametrize(
    "cmdline_args, report_ctx",
    (
        # Case 1, noop
        (
            tuple(),
            [
                (
                    "Multitest",
                    [
                        (
                            "Beta",
                            [
                                "test_ccc",
                                "test_xxx",
                                (
                                    "test_bbb",
                                    ["test_bbb <val=0>", "test_bbb <val=1>"],
                                ),
                                "test_aaa",
                                (
                                    "test_yyy",
                                    [
                                        "test_yyy <val=3>",
                                        "test_yyy <val=2>",
                                        "test_yyy <val=1>",
                                    ],
                                ),
                            ],
                        ),
                        ("Alpha", ["test_ccc", "test_bbb", "test_aaa"]),
                    ],
                )
            ],
        ),
        # Case 2, shuffle all
        (
            ("--shuffle", "all", "--shuffle-seed", "7"),
            [
                (
                    "Multitest",
                    [
                        (
                            "Beta",
                            [
                                (
                                    "test_yyy",
                                    [
                                        "test_yyy <val=1>",
                                        "test_yyy <val=3>",
                                        "test_yyy <val=2>",
                                    ],
                                ),
                                "test_ccc",
                                "test_aaa",
                                "test_xxx",
                                (
                                    "test_bbb",
                                    ["test_bbb <val=0>", "test_bbb <val=1>"],
                                ),
                            ],
                        ),
                        ("Alpha", ["test_aaa", "test_ccc", "test_bbb"]),
                    ],
                )
            ],
        ),
        # Case 3 shuffle suites & testcases
        (
            ("--shuffle", "suites", "testcases", "--shuffle-seed", "7"),
            [
                (
                    "Multitest",
                    [
                        (
                            "Beta",
                            [
                                (
                                    "test_yyy",
                                    [
                                        "test_yyy <val=1>",
                                        "test_yyy <val=3>",
                                        "test_yyy <val=2>",
                                    ],
                                ),
                                "test_ccc",
                                "test_aaa",
                                "test_xxx",
                                (
                                    "test_bbb",
                                    ["test_bbb <val=0>", "test_bbb <val=1>"],
                                ),
                            ],
                        ),
                        ("Alpha", ["test_aaa", "test_ccc", "test_bbb"]),
                    ],
                )
            ],
        ),
        # Case 4, shuffle suites
        (
            ("--shuffle", "suites", "--shuffle-seed", "7"),
            [
                (
                    "Multitest",
                    [
                        (
                            "Beta",
                            [
                                "test_ccc",
                                "test_xxx",
                                (
                                    "test_bbb",
                                    ["test_bbb <val=0>", "test_bbb <val=1>"],
                                ),
                                "test_aaa",
                                (
                                    "test_yyy",
                                    [
                                        "test_yyy <val=3>",
                                        "test_yyy <val=2>",
                                        "test_yyy <val=1>",
                                    ],
                                ),
                            ],
                        ),
                        ("Alpha", ["test_ccc", "test_bbb", "test_aaa"]),
                    ],
                )
            ],
        ),
        # Case 5, shuffle testcases
        (
            ("--shuffle", "testcases", "--shuffle-seed", "7"),
            [
                (
                    "Multitest",
                    [
                        (
                            "Beta",
                            [
                                (
                                    "test_yyy",
                                    [
                                        "test_yyy <val=1>",
                                        "test_yyy <val=3>",
                                        "test_yyy <val=2>",
                                    ],
                                ),
                                "test_ccc",
                                "test_aaa",
                                "test_xxx",
                                (
                                    "test_bbb",
                                    ["test_bbb <val=0>", "test_bbb <val=1>"],
                                ),
                            ],
                        ),
                        ("Alpha", ["test_aaa", "test_ccc", "test_bbb"]),
                    ],
                )
            ],
        ),
    ),
)
def test_command_line_ordering(cmdline_args, report_ctx):

    multitest = MultiTest(name="Multitest", suites=[Beta(), Alpha()])

    with argv_overridden(*cmdline_args):
        plan = TestplanMock(name="plan", parse_cmdline=True)
        plan.add(multitest)
        plan.run()

    test_report = plan.report
    check_report_context(test_report, report_ctx)
