import json
from functools import partial
from pathlib import Path

import boltons.iterutils
import pytest

from testplan import TestplanMock
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.common.utils.testing import (
    argv_overridden,
    captured_logging,
    to_stdout,
)
from testplan.testing import filtering, listing, ordering
from testplan.testing.listing import SimpleJsonLister
from testplan.testing.multitest import MultiTest, testcase, testsuite


@testsuite
class Alpha:
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
class Beta:
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
class Gamma:
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
    "  Primary:Beta  --tags color=yellow",
    "    Primary:Beta:test_c",
    "    Primary:Beta:test_b  --tags foo",
    "    Primary:Beta:test_a  --tags color=red",
    "  Primary:Alpha",
    "    Primary:Alpha:test_c",
    "    Primary:Alpha:test_b  --tags bar foo",
    "    Primary:Alpha:test_a  --tags color=green",
    "Secondary",
    "  Secondary:Gamma",
    "    Secondary:Gamma:test_c",
    "    Secondary:Gamma:test_b  --tags bar",
    "    Secondary:Gamma:test_a  --tags color=blue",
)

PATTERN_OUTPUT_WITH_PARTS = to_stdout(
    "Primary - part(0/2)",
    "  Primary - part(0/2):Beta  --tags color=yellow",
    "    Primary - part(0/2):Beta:test_c",
    "    Primary - part(0/2):Beta:test_a  --tags color=red",
    "  Primary - part(0/2):Alpha",
    "    Primary - part(0/2):Alpha:test_c",
    "    Primary - part(0/2):Alpha:test_a  --tags color=green",
    "Primary - part(1/2)",
    "  Primary - part(1/2):Beta  --tags color=yellow",
    "    Primary - part(1/2):Beta:test_b  --tags foo",
    "  Primary - part(1/2):Alpha",
    "    Primary - part(1/2):Alpha:test_b  --tags bar foo",
    "Secondary",
    "  Secondary:Gamma",
    "    Secondary:Gamma:test_c",
    "    Secondary:Gamma:test_b  --tags bar",
    "    Secondary:Gamma:test_a  --tags color=blue",
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


def prepare_plan(plan, prim_parts):
    if prim_parts == 1:
        plan.add(MultiTest(name="Primary", suites=[Beta(), Alpha()]))
    else:
        for i in range(prim_parts):
            plan.add(
                MultiTest(
                    name="Primary",
                    suites=[Beta(), Alpha()],
                    part=(i, prim_parts),
                )
            )
    plan.add(MultiTest(name="Secondary", suites=[Gamma()]))


@pytest.mark.parametrize(
    "listing_obj,filter_obj,sorter_obj,prim_parts,expected_output",
    [
        # Basic name listing
        (
            listing.ExpandedNameLister(),
            filtering.Filter(),
            ordering.NoopSorter(),
            1,
            DEFAULT_NAME_OUTPUT,
        ),
        # Basic pattern listing
        (
            listing.ExpandedPatternLister(),
            filtering.Filter(),
            ordering.NoopSorter(),
            1,
            DEFAULT_PATTERN_OUTPUT,
        ),
        # Basic count listing
        (
            listing.CountLister(),
            filtering.Filter(),
            ordering.NoopSorter(),
            1,
            to_stdout(
                "Primary: (2 suites, 6 testcases)",
                "Secondary: (1 suite, 3 testcases)",
            ),
        ),
        # Basic pattern listing with MultiTest parts
        (
            listing.ExpandedPatternLister(),
            filtering.Filter(),
            ordering.NoopSorter(),
            2,
            PATTERN_OUTPUT_WITH_PARTS,
        ),
        # Custom sort & name listing
        (
            listing.ExpandedNameLister(),
            filtering.Filter(),
            ordering.AlphanumericSorter(),
            1,
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
            1,
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
    runpath, listing_obj, filter_obj, sorter_obj, prim_parts, expected_output
):
    plan = TestplanMock(
        name="plan",
        test_lister=listing_obj,
        test_filter=filter_obj,
        test_sorter=sorter_obj,
        runpath=runpath,
    )

    with captured_logging(TESTPLAN_LOGGER) as log_capture:
        prepare_plan(plan, prim_parts)
        assert log_capture.output == expected_output

        result = plan.run()
        assert len(result.test_report) == 0, "No tests should be run."


@pytest.mark.parametrize(
    "cmdline_args,prim_parts,expected_output",
    [
        (["--list"], 1, DEFAULT_NAME_OUTPUT),
        (["--info", "pattern"], 1, DEFAULT_PATTERN_OUTPUT),
        (["--info", "pattern"], 2, PATTERN_OUTPUT_WITH_PARTS),
        (["--info", "name"], 1, DEFAULT_NAME_OUTPUT),
        (
            ["--info", "name", "--patterns", "*:Alpha", "*:Beta:test_c"],
            2,
            to_stdout(
                "Primary - part(0/2)",
                "  Beta",
                "    test_c",
                "  Alpha",
                "    test_c",
                "    test_a",
                "Primary - part(1/2)",
                "  Alpha",
                "    test_b",
            ),
        ),
    ],
)
def test_command_line_listing(
    runpath, cmdline_args, prim_parts, expected_output
):

    with argv_overridden(*cmdline_args):
        plan = TestplanMock(name="plan", parse_cmdline=True, runpath=runpath)

        with captured_logging(TESTPLAN_LOGGER) as log_capture:
            prepare_plan(plan, prim_parts)
            assert log_capture.output == expected_output

            result = plan.run()
            assert len(result.test_report) == 0, "No tests should be run."


NUM_TESTS = 100


@testsuite
class ParametrizedSuite:
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
                *["Primary", "  Primary:ParametrizedSuite"]
                + [
                    "    Primary:ParametrizedSuite"
                    ":test_method <val={}>".format(idx)
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


def validate_json_result(result_json):
    result = json.loads(result_json)

    expected = {
        "name": "plan",
        "tests.0.name": "Primary",
        "tests.0.id": "Primary",
        "tests.0.test_suites.0.name": "Beta",
        "tests.0.test_suites.0.id": "Primary:Beta",
        "tests.0.test_suites.0.location.file": __file__,
        "tests.0.test_suites.0.test_cases.0.name": "test_a",
        "tests.0.test_suites.0.test_cases.0.id": "Primary:Beta:test_a",
        "tests.0.test_suites.0.test_cases.0.location.file": __file__,
        "tests.0.test_suites.0.test_cases.1.name": "test_b",
        "tests.0.test_suites.0.test_cases.1.id": "Primary:Beta:test_b",
        "tests.0.test_suites.0.test_cases.1.location.file": __file__,
        "tests.0.test_suites.0.test_cases.2.name": "test_c",
        "tests.0.test_suites.0.test_cases.2.id": "Primary:Beta:test_c",
        "tests.0.test_suites.0.test_cases.2.location.file": __file__,
        "tests.0.test_suites.1.name": "Alpha",
        "tests.0.test_suites.1.id": "Primary:Alpha",
        "tests.0.test_suites.1.test_cases.0.name": "test_a",
        "tests.0.test_suites.1.test_cases.0.id": "Primary:Alpha:test_a",
        "tests.0.test_suites.1.test_cases.1.name": "test_b",
        "tests.0.test_suites.1.test_cases.1.id": "Primary:Alpha:test_b",
        "tests.1.name": "Secondary",
        "tests.1.id": "Secondary",
        "tests.1.test_suites.0.name": "Gamma",
        "tests.1.test_suites.0.id": "Secondary:Gamma",
        "tests.1.test_suites.0.test_cases.0.name": "test_a",
        "tests.1.test_suites.0.test_cases.0.id": "Secondary:Gamma:test_a",
        "tests.1.test_suites.0.test_cases.1.name": "test_b",
        "tests.1.test_suites.0.test_cases.1.id": "Secondary:Gamma:test_b",
        "tests.1.test_suites.0.test_cases.2.name": "test_c",
        "tests.1.test_suites.0.test_cases.2.id": "Secondary:Gamma:test_c",
    }
    for path, expected_value in expected.items():
        assert (
            boltons.iterutils.get_path(result, path.split("."))
            == expected_value
        )


def test_json_listing(runpath):

    main = TestplanMock.main_wrapper(
        name="plan",
        test_lister=SimpleJsonLister(),
        runpath=runpath,
        parse_cmdline=False,
    )(partial(prepare_plan, prim_parts=1))

    with captured_logging(TESTPLAN_LOGGER) as log_capture:
        main()

        result = log_capture.output
        validate_json_result(result)


def test_json_listing_to_file(runpath):
    result_path = Path(runpath) / "test.json"
    main = TestplanMock.main_wrapper(
        name="plan",
        test_lister=SimpleJsonLister(),
        test_lister_output=str(result_path),
        runpath=runpath,
        parse_cmdline=False,
    )(partial(prepare_plan, prim_parts=1))

    main()

    result = result_path.read_text()
    validate_json_result(result)
