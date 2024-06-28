import os
import tempfile

import pytest

from testplan import TestplanMock
from testplan.common.utils.testing import argv_overridden, check_report_context
from testplan.runners.pools.base import Pool
from testplan.testing import filtering
from testplan.testing.multitest import MultiTest, testcase, testsuite


@testsuite(tags="foo")
class Alpha:
    @testcase
    def test_one(self, env, result):
        pass

    @testcase(tags={"color": "blue"})
    def test_two(self, env, result):
        pass

    @testcase(tags={"color": "red"})
    def test_three(self, env, result):
        pass


@testsuite(tags=("foo", "bar"))
class Beta:
    @testcase
    def test_one(self, env, result):
        pass

    @testcase(tags={"color": "red"})
    def test_two(self, env, result):
        pass

    @testcase(tags={"color": "green"})
    def test_three(self, env, result):
        pass


@testsuite(tags=("foo", "baz"))
class Gamma:
    @testcase
    def test_one(self, env, result):
        pass

    @testcase(tags={"color": ("blue", "yellow")})
    def test_two(self, env, result):
        pass

    @testcase(tags={"color": ("red", "green")})
    def test_three(self, env, result):
        pass


@pytest.fixture
def filter_file():
    f = tempfile.NamedTemporaryFile(delete=False)
    f.close()
    try:
        fp = open(f.name, "w+")
        yield fp
    finally:
        fp.close()
        os.unlink(f.name)


@pytest.mark.parametrize(
    "filter_obj, report_ctx",
    (
        # Case 1
        (
            filtering.Filter(),
            [
                (
                    "XXX",
                    [
                        ("Alpha", ["test_one", "test_two", "test_three"]),
                        ("Beta", ["test_one", "test_two", "test_three"]),
                    ],
                ),
                ("YYY", (("Gamma", ["test_one", "test_two", "test_three"]),)),
            ],
        ),
        # Case 2
        (
            filtering.Pattern("*:*:test_two"),
            [
                ("XXX", [("Alpha", ["test_two"]), ("Beta", ["test_two"])]),
                ("YYY", [("Gamma", ["test_two"])]),
            ],
        ),
        # Case 3
        (
            filtering.Pattern("XXX:Beta:test_two"),
            [("XXX", [("Beta", ["test_two"])])],
        ),
        # Case 4 - testcase name match AND tag match
        (
            filtering.And(
                filtering.Pattern("*:*:test_two"),
                filtering.Tags({"color": "blue"}),
            ),
            [
                ("XXX", [("Alpha", ["test_two"])]),
                ("YYY", [("Gamma", ["test_two"])]),
            ],
        ),
        # Case 5 - testcase name match AND tag match, different syntax
        (
            (
                filtering.Pattern("*:*:test_two")
                and filtering.Tags({"color": "blue"})
            ),
            [
                ("XXX", [("Alpha", ["test_two"])]),
                ("YYY", [("Gamma", ["test_two"])]),
            ],
        ),
        #  Case 6 - Run tests that are:
        # named `test_one` AND tagged with `baz`
        # OR
        # belong to a suite named Alpha OR Beta AND tagged with `color`: `red`
        (
            filtering.Or(
                filtering.And(
                    filtering.Pattern("*:*:test_one"), filtering.Tags("baz")
                ),
                filtering.And(
                    filtering.Pattern.any("*:Alpha:*", "*:Beta:*"),
                    filtering.Tags({"color": "red"}),
                ),
            ),
            [
                ("XXX", [("Alpha", ["test_three"]), ("Beta", ["test_two"])]),
                ("YYY", [("Gamma", ["test_one"])]),
            ],
        ),
        #  Case 7, same as case 6, different syntax
        (
            (
                (filtering.Pattern("*:*:test_one") & filtering.Tags("baz"))
                | (
                    filtering.Pattern.any("*:Alpha:*", "*:Beta:*")
                    & filtering.Tags({"color": "red"})
                )
            ),
            [
                ("XXX", [("Alpha", ["test_three"]), ("Beta", ["test_two"])]),
                ("YYY", [("Gamma", ["test_one"])]),
            ],
        ),
        # Case 8, inverse filter via Not
        (
            filtering.Not(filtering.Pattern("*:*:test_one")),
            [
                (
                    "XXX",
                    [
                        ("Alpha", ["test_two", "test_three"]),
                        ("Beta", ["test_two", "test_three"]),
                    ],
                ),
                ("YYY", (("Gamma", ["test_two", "test_three"]),)),
            ],
        ),
        # Case 9, Same as case 8, different syntax
        (
            ~filtering.Pattern("*:*:test_one"),
            [
                (
                    "XXX",
                    [
                        ("Alpha", ["test_two", "test_three"]),
                        ("Beta", ["test_two", "test_three"]),
                    ],
                ),
                ("YYY", (("Gamma", ["test_two", "test_three"]),)),
            ],
        ),
    ),
)
def test_programmatic_filtering(filter_obj, report_ctx):
    multitest_x = MultiTest(name="XXX", suites=[Alpha(), Beta()])
    multitest_y = MultiTest(name="YYY", suites=[Gamma()])

    plan = TestplanMock(name="plan", test_filter=filter_obj)
    plan.add(multitest_x)
    plan.add(multitest_y)
    plan.run()

    test_report = plan.report
    check_report_context(test_report, report_ctx)


@pytest.mark.parametrize(
    "filter_obj, report_ctx",
    (
        # Case 1, part not specified
        (
            filtering.Pattern("XXX:Alpha:test_one")
            | filtering.Pattern("XXX:Alpha:test_two"),
            [
                ("XXX - part(0/3)", [("Alpha", ["test_one"])]),
                ("XXX - part(1/3)", [("Alpha", ["test_two"])]),
            ],
        ),
        # Case 2, part specified
        (
            filtering.Pattern("XXX - part(0/3):Alpha:test_one")
            | filtering.Pattern("XXX - part(0/3):Beta:test_three"),
            [
                ("XXX - part(0/3)", [("Alpha", ["test_one"])]),
            ],
        ),
        # Case 3, unix filename pattern in part
        (
            filtering.Pattern("XXX - part([012]/*):Alpha")
            | filtering.Pattern("XXX:Beta:test_three"),
            [
                (
                    "XXX - part(0/3)",
                    [("Alpha", ["test_one"]), ("Beta", ["test_three"])],
                ),
                ("XXX - part(1/3)", [("Alpha", ["test_two"])]),
                ("XXX - part(2/3)", [("Alpha", ["test_three"])]),
            ],
        ),
        # Case 4, ill-formed part
        (
            filtering.Pattern("XXX - part*"),
            [],
        ),
    ),
)
def test_programmatic_filtering_with_parts(filter_obj, report_ctx):
    plan = TestplanMock(name="plan", test_filter=filter_obj)
    for i in range(0, 3):
        plan.add(MultiTest(name="XXX", suites=[Alpha(), Beta()], part=(i, 3)))
    plan.run()

    test_report = plan.report
    check_report_context(test_report, report_ctx)


@pytest.mark.parametrize(
    "filter_obj, num_parts, report_ctx",
    (
        (
            filtering.Pattern("XXX - part(0/3)")
            | filtering.Pattern("XXX - part(1/3)"),
            3,
            [
                (
                    "XXX",
                    [
                        ("Alpha", ["test_one", "test_two"]),
                        ("Beta", ["test_one", "test_two"]),
                    ],
                ),
            ],
        ),
        (
            filtering.Pattern("XXX:Alpha") | filtering.Pattern("XXX:Beta"),
            2,
            [
                (
                    "XXX",
                    [
                        ("Alpha", ["test_one", "test_two", "test_three"]),
                        ("Beta", ["test_one", "test_two", "test_three"]),
                    ],
                ),
            ],
        ),
        # as parts being a runtime-only feature, specifying part in patterns
        # having suite-level or case-level is a bad idea, nevertheless the
        # following one works intuitively
        (
            filtering.Pattern("XXX - part(0/2):Alpha")
            | filtering.Pattern("XXX - part(1/2):Beta"),
            2,
            [
                (
                    "XXX",
                    [
                        ("Alpha", ["test_one", "test_three"]),
                        ("Beta", ["test_two"]),
                    ],
                ),
            ],
        ),
        # the following one serves as an example of unexpected outcome
        # here's why:
        #   user's perspective
        #       one only wants Alpha cases from part 0 (p0) together with all Beta
        #       cases, one's expectation would be
        #           p0 <= a1 a3 b2
        #           p1 <= b1 b3
        #           merged <= a1 a3 b1 b2 b3
        #   p0's perspective:
        #       p0 is able to collect all cases, after parting, p0 thinks
        #           p0 <= a1 a3 b2
        #           p1 <= a2 b1 b3
        #       p0 will execute a1 a3 b2
        #   p1's perspective:
        #       p1 could only collect Beta cases, since part number being encoded in
        #       input pattern, after parting, p1 thinks
        #           p0 <= b1 b3
        #           p1 <= b2
        #       p1 will only execute b2
        #   after merged, user will only get a1 a3 b2, mismatch expectation!
        (
            filtering.Pattern("XXX - part(0/2):Alpha")
            | filtering.Pattern("XXX:Beta"),
            2,
            [
                (
                    "XXX",
                    [
                        ("Alpha", ["test_one", "test_three"]),
                        ("Beta", ["test_two"]),
                    ],
                ),
            ],
        ),
        # the following one servers as another example of unexpected outcome
        (
            filtering.Pattern("XXX - part(0/2):Beta:test_one")
            | filtering.Pattern("XXX - part(0/2):Beta:test_two"),
            2,
            [("XXX", [("Beta", ["test_one"])])],
        ),
    ),
)
def test_programmatic_filtering_with_parts_merged(
    filter_obj, num_parts, report_ctx
):
    plan = TestplanMock(
        name="plan", test_filter=filter_obj, merge_scheduled_parts=True
    )
    plan.add_resource(Pool(name="tpool"))
    for i in range(num_parts):
        plan.schedule(
            target=MultiTest(
                name="XXX", suites=[Alpha(), Beta()], part=(i, num_parts)
            ),
            resource="tpool",
        )
    plan.run()

    test_report = plan.report
    check_report_context(test_report, report_ctx)


@pytest.mark.parametrize(
    "cmdline_args, report_ctx",
    (
        # Case 1, no filtering args, full report ctx expected
        (
            tuple(),
            [
                (
                    "XXX",
                    [
                        ("Alpha", ["test_one", "test_two", "test_three"]),
                        ("Beta", ["test_one", "test_two", "test_three"]),
                    ],
                ),
                ("YYY", (("Gamma", ["test_one", "test_two", "test_three"]),)),
            ],
        ),
        # Case 2, pattern filtering
        (
            ("--patterns", "XXX:*:test_two"),
            [("XXX", [("Alpha", ["test_two"]), ("Beta", ["test_two"])])],
        ),
        # Case 3, pattern filtering (multiple params)
        (
            ("--patterns", "XXX:*:test_two", "--patterns", "YYY:*:test_three"),
            [
                ("XXX", [("Alpha", ["test_two"]), ("Beta", ["test_two"])]),
                ("YYY", (("Gamma", ["test_three"]),)),
            ],
        ),
        # Case 4, tag filtering
        (
            ("--tags", "bar", "color=red"),
            [
                (
                    "XXX",
                    [
                        ("Alpha", ["test_three"]),
                        ("Beta", ["test_one", "test_two", "test_three"]),
                    ],
                ),
                ("YYY", (("Gamma", ["test_three"]),)),
            ],
        ),
        # Case 5, tag filtering (multiple params)
        (
            # Run tests that match ANY of these rules
            # as they belong to the same category (tags)
            (
                "--tags",
                "bar",
                "color=blue",  # bar OR color=blue
                "--tags-all",
                "baz",
                "color=red",  # baz AND color=red
            ),
            [
                (
                    "XXX",
                    [
                        ("Alpha", ["test_two"]),
                        ("Beta", ["test_one", "test_two", "test_three"]),
                    ],
                ),
                ("YYY", (("Gamma", ["test_two", "test_three"]),)),
            ],
        ),
        # Case 6, pattern & tag composite filtering
        # Tag filters will be wrapped by Any
        # Pattern and tag filters will be wrapped by All
        (
            (
                "--patterns",
                "*:*:test_one",
                "*:*:test_three",
                "--tags",
                "bar",
                "color=blue",  # bar OR color=blue
                "--tags-all",
                "baz",
                "color=red",  # baz AND color=red
            ),
            [
                ("XXX", [("Beta", ["test_one", "test_three"])]),
                ("YYY", (("Gamma", ["test_three"]),)),
            ],
        ),
        # Case 7, pattern filtering for empty run
        (
            ("--patterns", "EmptyRun"),
            [],
        ),
    ),
)
def test_command_line_filtering(cmdline_args, report_ctx):

    multitest_x = MultiTest(name="XXX", suites=[Alpha(), Beta()])
    multitest_y = MultiTest(name="YYY", suites=[Gamma()])

    with argv_overridden(*cmdline_args):
        plan = TestplanMock(name="plan", parse_cmdline=True)
        plan.add(multitest_x)
        plan.add(multitest_y)
        plan.run()

    test_report = plan.report
    check_report_context(test_report, report_ctx)

    if not test_report.entries:
        assert plan.result.success


@pytest.mark.parametrize(
    "lines, report_ctx",
    (
        # Case 1, single line of pattern
        (
            ["XXX:*:test_two"],
            [("XXX", [("Alpha", ["test_two"]), ("Beta", ["test_two"])])],
        ),
        # Case 2, multiple lines of pattern
        (
            ["XXX:*:test_two", "YYY:*:test_three"],
            [
                ("XXX", [("Alpha", ["test_two"]), ("Beta", ["test_two"])]),
                ("YYY", (("Gamma", ["test_three"]),)),
            ],
        ),
    ),
)
def test_command_line_filtering_file(lines, report_ctx, request):
    # special case of test_command_line_filtering, with filter in a temp file

    # NOTE: to use fixture in parametrized tests
    filter_file = request.getfixturevalue("filter_file")
    for l in lines:
        filter_file.write(l + "\n")
    filter_file.flush()

    multitest_x = MultiTest(name="XXX", suites=[Alpha(), Beta()])
    multitest_y = MultiTest(name="YYY", suites=[Gamma()])

    with argv_overridden("--patterns-file", filter_file.name):
        plan = TestplanMock(name="plan", parse_cmdline=True)
        plan.add(multitest_x)
        plan.add(multitest_y)
        plan.run()

    test_report = plan.report
    check_report_context(
        test_report,
        report_ctx,
    )

    if not test_report.entries:
        assert plan.result.success
