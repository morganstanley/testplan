import pytest

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import TestplanMock
from testplan.common.utils.testing import (
    captured_logging,
    argv_overridden,
    to_stdout,
)
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.testing import listing, filtering, ordering


@testsuite
class Alpha(object):
    @testcase
    def test_c(self, env, result):
        pass

    @testcase(tags=("foo", "bar"))
    def test_b(self, env, result):
        pass

    @testcase(tags={"color": "green"})
    def test_a(self, env, result):
        pass


@testsuite(tags={"color": "yellow"})
class Beta(object):
    @testcase
    def test_c(self, env, result):
        pass

    @testcase(tags="foo")
    def test_b(self, env, result):
        pass

    @testcase(tags={"color": "red"})
    def test_a(self, env, result):
        pass


@testsuite
class Gamma(object):
    @testcase
    def test_c(self, env, result):
        pass

    @testcase(tags="bar")
    def test_b(self, env, result):
        pass

    @testcase(tags={"color": "blue"})
    def test_a(self, env, result):
        pass


DEFAULT_PATTERN_OUTPUT = to_stdout(
    "Primary",
    "  Primary::Beta  --tags color=yellow",
    "    Primary::Beta::test_c",
    "    Primary::Beta::test_b  --tags foo",
    "    Primary::Beta::test_a  --tags color=red",
    "  Primary::Alpha",
    "    Primary::Alpha::test_c",
    "    Primary::Alpha::test_b  --tags bar foo",
    "    Primary::Alpha::test_a  --tags color=green",
    "Secondary",
    "  Secondary::Gamma",
    "    Secondary::Gamma::test_c",
    "    Secondary::Gamma::test_b  --tags bar",
    "    Secondary::Gamma::test_a  --tags color=blue",
)


DEFAULT_NAME_OUTPUT = to_stdout(
    "Primary",
    "  Beta",
    "    test_c",
    "    test_b",
    "    test_a",
    "  Alpha",
    "    test_c",
    "    test_b",
    "    test_a",
    "Secondary",
    "  Gamma",
    "    test_c",
    "    test_b",
    "    test_a",
)


@pytest.mark.parametrize(
    "listing_obj,filter_obj,sorter_obj,expected_output",
    [
        # Basic name listing
        (
            listing.ExpandedNameLister(),
            filtering.Filter(),
            ordering.NoopSorter(),
            DEFAULT_NAME_OUTPUT,
        ),
        # Basic pattern listing
        (
            listing.ExpandedPatternLister(),
            filtering.Filter(),
            ordering.NoopSorter(),
            DEFAULT_PATTERN_OUTPUT,
        ),
        # Basic count listing
        (
            listing.CountLister(),
            filtering.Filter(),
            ordering.NoopSorter(),
            to_stdout(
                "Primary: (2 suites, 6 testcases)",
                "Secondary: (1 suite, 3 testcases)",
            ),
        ),
        # Custom sort & name listing
        (
            listing.ExpandedNameLister(),
            filtering.Filter(),
            ordering.AlphanumericSorter(),
            to_stdout(
                "Primary",
                "  Alpha",
                "    test_a",
                "    test_b",
                "    test_c",
                "  Beta",
                "    test_a",
                "    test_b",
                "    test_c",
                "Secondary",
                "  Gamma",
                "    test_a",
                "    test_b",
                "    test_c",
            ),
        ),
        # Custom sort / Custom filter / name listing
        (
            listing.ExpandedNameLister(),
            filtering.Pattern("*:Alpha") | filtering.Pattern("*:Beta"),
            ordering.AlphanumericSorter(),
            to_stdout(
                "Primary",
                "  Alpha",
                "    test_a",
                "    test_b",
                "    test_c",
                "  Beta",
                "    test_a",
                "    test_b",
                "    test_c",
            ),
        ),
    ],
)
def test_programmatic_listing(
    runpath, listing_obj, filter_obj, sorter_obj, expected_output
):
    multitest_x = MultiTest(name="Primary", suites=[Beta(), Alpha()])
    multitest_y = MultiTest(name="Secondary", suites=[Gamma()])

    plan = TestplanMock(
        name="plan",
        test_lister=listing_obj,
        test_filter=filter_obj,
        test_sorter=sorter_obj,
        runpath=runpath,
    )

    with captured_logging(TESTPLAN_LOGGER) as log_capture:
        plan.add(multitest_x)
        plan.add(multitest_y)

        assert log_capture.output == expected_output

        result = plan.run()
        assert len(result.test_report) == 0, "No tests should be run."


@pytest.mark.parametrize(
    "cmdline_args,expected_output",
    [
        (["--list"], DEFAULT_NAME_OUTPUT),
        (["--info", "pattern"], DEFAULT_PATTERN_OUTPUT),
        (["--info", "name"], DEFAULT_NAME_OUTPUT),
        (
            ["--info", "name", "--patterns", "*:Alpha", "*:Beta:test_c"],
            to_stdout(
                "Primary",
                "  Beta",
                "    test_c",
                "  Alpha",
                "    test_c",
                "    test_b",
                "    test_a",
            ),
        ),
    ],
)
def test_command_line_listing(runpath, cmdline_args, expected_output):
    multitest_x = MultiTest(name="Primary", suites=[Beta(), Alpha()])
    multitest_y = MultiTest(name="Secondary", suites=[Gamma()])

    with argv_overridden(*cmdline_args):
        plan = TestplanMock(name="plan", parse_cmdline=True, runpath=runpath)

        with captured_logging(TESTPLAN_LOGGER) as log_capture:
            plan.add(multitest_x)
            plan.add(multitest_y)

            result = plan.run()

            assert log_capture.output == expected_output
            assert len(result.test_report) == 0, "No tests should be run."


NUM_TESTS = 100


@testsuite
class ParametrizedSuite(object):
    @testcase(parameters=list(range(NUM_TESTS)))
    def test_method(self, env, result, val):
        pass


@pytest.mark.parametrize(
    "listing_obj,expected_output",
    [
        # No trim
        (
            listing.ExpandedNameLister(),
            to_stdout(
                *["Primary", "  ParametrizedSuite"]
                + [
                    "    test_method <val={}>".format(idx)
                    for idx in range(NUM_TESTS)
                ]
            ),
        ),
        # Trimmed names
        (
            listing.NameLister(),
            to_stdout(
                *["Primary", "  ParametrizedSuite"]
                + [
                    "    test_method <val={}>".format(idx)
                    for idx in range(listing.MAX_TESTCASES)
                ]
                + [
                    "    ... {} more testcases ...".format(
                        NUM_TESTS - listing.MAX_TESTCASES
                    )
                ]
            ),
        ),
        # Trimmed patterns
        (
            listing.PatternLister(),
            to_stdout(
                *["Primary", "  Primary::ParametrizedSuite"]
                + [
                    "    Primary::ParametrizedSuite"
                    "::test_method <val={}>".format(idx)
                    for idx in range(listing.MAX_TESTCASES)
                ]
                + [
                    "    ... {} more testcases ...".format(
                        NUM_TESTS - listing.MAX_TESTCASES
                    )
                ]
            ),
        ),
    ],
)
def test_testcase_trimming(runpath, listing_obj, expected_output):
    multitest_x = MultiTest(name="Primary", suites=[ParametrizedSuite()])

    plan = TestplanMock(name="plan", test_lister=listing_obj, runpath=runpath)

    with captured_logging(TESTPLAN_LOGGER) as log_capture:
        plan.add(multitest_x)

        assert log_capture.output == expected_output

        result = plan.run()
        assert len(result.test_report) == 0, "No tests should be run."
