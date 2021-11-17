"""Unit tests for the testplan.testing.multitest.result module."""

import os
import re
import copy
import hashlib
import collections
from unittest import mock

import pytest
import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plot

from testplan.testing.multitest import result as result_mod
from testplan.testing.multitest.suite import testcase, testsuite
from testplan.testing.multitest import MultiTest
from testplan.common.utils import comparison
from testplan.common.utils import testing
from testplan.common.utils import path as path_utils


@testsuite
class AssertionOrder(object):
    @testcase
    def case(self, env, result):
        summary = result.subresult()
        first = result.subresult()
        second = result.subresult()

        second.true(True, "AssertionSecond")

        result.true(True, "AssertionMain1")
        result.true(True, "AssertionMain2")

        first.true(True, "AssertionFirst1")
        first.true(True, "AssertionFirst2")

        summary.append(first)
        result.true(first.passed, "Report passed so far.")
        if first.passed:
            summary.append(second)

        result.prepend(summary)


def test_assertion_orders():
    mtest = MultiTest(name="AssertionsOrder", suites=[AssertionOrder()])
    mtest.run()

    expected = [
        "AssertionFirst1",
        "AssertionFirst2",
        "AssertionSecond",
        "AssertionMain1",
        "AssertionMain2",
        "Report passed so far.",
    ]
    # pylint: disable=invalid-sequence-index
    assertions = (
        entry
        for entry in mtest.report.flatten()
        if isinstance(entry, dict) and entry["meta_type"] == "assertion"
    )

    for idx, entry in enumerate(assertions):
        assert entry["description"] == expected[idx]


@pytest.fixture
def dict_ns():
    """Dict namespace with a mocked out result object."""
    mock_result = mock.MagicMock()
    mock_result.entries = collections.deque()
    return result_mod.DictNamespace(mock_result)


@pytest.fixture
def fix_ns():
    """FIX namespace with a mocked out result object."""
    mock_result = mock.MagicMock()
    mock_result.entries = collections.deque()
    return result_mod.FixNamespace(mock_result)


class TestDictNamespace(object):
    """Unit testcases for the result.DictNamespace class."""

    def test_basic_match(self, dict_ns):
        """
        Test the match method against identical expected and actual dicts.
        """
        expected = {"key": 123}
        actual = expected.copy()

        assert dict_ns.match(
            actual,
            expected,
            description="Basic dictmatch of identical dicts passes",
        )

        assert dict_ns.match(
            actual,
            expected,
            description="Force type-check of values",
            value_cmp_func=comparison.COMPARE_FUNCTIONS["check_types"],
        )

        assert dict_ns.match(
            actual,
            expected,
            description="Convert values to strings before comparing",
            value_cmp_func=comparison.COMPARE_FUNCTIONS["stringify"],
        )

    def test_duck_match(self, dict_ns):
        """
        Test the match method by seting different types that can be compared.
        Due to duck-typing, ints and floats can be equal if they refer to the
        same numeric value - in this case, 123 == 123.0. However if
        type-checking is forced by use of the check_types comparison method
        the assertion will fail.
        """
        expected = {"key": 123}
        actual = {"key": 123.0}

        assert dict_ns.match(
            actual,
            expected,
            description="Dictmatch passes since the numeric values are equal.",
        )

        assert not dict_ns.match(
            actual,
            expected,
            description="Dictmatch fails when type comparison is forced.",
            value_cmp_func=comparison.COMPARE_FUNCTIONS["check_types"],
        )

        assert not dict_ns.match(
            actual,
            expected,
            description="Dictmatch with string conversion fails due to "
            "different string representations of int/float.",
            value_cmp_func=comparison.COMPARE_FUNCTIONS["stringify"],
        )

    def test_fail_match(self, dict_ns):
        """
        Test the match method for types that do not compare equal - in this
        case, 123 should not match "123".
        """
        expected = {"key": 123}
        actual = {"key": "123"}

        assert not dict_ns.match(
            actual, expected, description='Dictmatch fails because 123 != "123'
        )

        assert not dict_ns.match(
            actual,
            expected,
            description="Dictmatch fails due to type mismatch",
            value_cmp_func=comparison.COMPARE_FUNCTIONS["check_types"],
        )

        assert dict_ns.match(
            actual,
            expected,
            description="Dictmatch passes when values are converted to strings",
            value_cmp_func=comparison.COMPARE_FUNCTIONS["stringify"],
        )

    def test_custom_match(self, dict_ns):
        """Test a dict match using a user-defined comparison function."""
        expected = {"key": 174.24}
        actual = {"key": 174.87}

        tolerance = 1.0

        def cmp_with_tolerance(lhs, rhs):
            """Check that both values are within a given tolerance range."""
            return abs(lhs - rhs) < tolerance

        assert not dict_ns.match(
            actual, expected, description="Values are not exactly equal"
        )

        assert dict_ns.match(
            actual,
            expected,
            description="Values are equal within tolerance",
            value_cmp_func=cmp_with_tolerance,
        )

    def test_report_modes(self, dict_ns):
        """Test controlling report modes for a dict match."""
        expected = {"key{}".format(i): i for i in range(10)}
        actual = expected.copy()
        expected["wrong"] = "expected"
        actual["wrong"] = "actual"

        assert not dict_ns.match(
            actual, expected, description="Keep all comparisons by default"
        )
        assert len(dict_ns.result.entries) == 1
        dict_assert = dict_ns.result.entries.popleft()
        assert len(dict_assert.comparison) == 11

        assert dict_ns.match(
            actual,
            expected,
            description="Keep ignored comparisons",
            include_keys=["key{}".format(i) for i in range(3)],
        )

        assert len(dict_ns.result.entries) == 1
        dict_assert = dict_ns.result.entries.popleft()
        assert len(dict_assert.comparison) == 11

        assert dict_ns.match(
            actual,
            expected,
            description="Discard ignored comparisons",
            include_keys=["key{}".format(i) for i in range(3)],
            report_mode=comparison.ReportOptions.NO_IGNORED,
        )

        assert len(dict_ns.result.entries) == 1
        dict_assert = dict_ns.result.entries.popleft()
        assert len(dict_assert.comparison) == 3

        assert not dict_ns.match(
            actual,
            expected,
            report_mode=comparison.ReportOptions.FAILS_ONLY,
            description="Discard passing comparisons",
        )
        assert len(dict_ns.result.entries) == 1
        dict_assert = dict_ns.result.entries.popleft()
        assert len(dict_assert.comparison) == 1

    def test_flattened_comparison_result(self, dict_ns):
        """Test the comparison result in flattened entries."""
        expected = {
            "foo": 1,
            "bar": lambda val: val >= 1,
            "baz": [
                {
                    "apple": 3,
                    "pear": 4,
                    "bat": [
                        {"wine": "gin", "tea": re.compile(r"[a-z]{5}")},
                        {"wine": "vodka", "tea": "green"},
                    ],
                }
            ],
        }
        actual = copy.deepcopy(expected)
        actual["bar"] = 2
        actual["baz"][0]["pear"] = 5
        actual["baz"][0]["bat"][0]["wine"] = "lime"
        actual["baz"][0]["bat"][0]["tea"] = "oolong"
        actual["baz"][0]["bat"][1]["wine"] = "brandy"
        actual["baz"][0]["bat"][1]["tea"] = "black"
        assert dict_ns.match(
            actual,
            expected,
            description="complex dictionary comparison",
            exclude_keys=["pear", "wine", "tea"],
        )
        assert len(dict_ns.result.entries) == 1

        # Comparison result is a list of list items in below format:
        # [indent, key, result, (act_type, act_value), (exp_type, exp_value)]
        comp_result = dict_ns.result.entries[0].comparison
        bar = [item for item in comp_result if item[1] == "bar"][0]
        assert bar[0] == 0 and bar[4][0] == "func"
        baz = [item for item in comp_result if item[1] == "baz"][0]
        assert baz[0] == 0 and baz[2][0].lower() == comparison.Match.PASS
        bat = [item for item in comp_result if item[1] == "bat"][0]
        assert bat[0] == 1 and bat[2][0].lower() == comparison.Match.IGNORED
        tea_1, tea_2 = [item for item in comp_result if item[1] == "tea"]
        assert (
            tea_1[0] == tea_2[0] == 2
            and tea_1[2][0].lower() == comparison.Match.IGNORED
            and tea_2[2][0].lower() == comparison.Match.IGNORED
            and tea_1[4][0] == "REGEX"
        )


class TestFIXNamespace(object):
    """Unit testcases for the result.FixNamespace class."""

    def test_untyped_fixmatch(self, fix_ns):
        """Test FIX matches between untyped FIX messages."""
        expected = testing.FixMessage(
            ((35, "D"), (38, "1000000"), (44, "125.83"))
        )
        actual = expected.copy()

        assert fix_ns.match(actual, expected, description="Basic FIX match")

    def test_typed_fixmatch(self, fix_ns):
        """Test FIX matches between typed FIX messages."""
        expected = testing.FixMessage(
            ((35, "D"), (38, 1000000), (44, 125.83)), typed_values=True
        )
        actual = expected.copy()

        assert fix_ns.match(actual, expected, description="Basic FIX match")

        # Now change the type of the actual 38 key's value to str. The assert
        # should fail since we are performing a typed match.
        actual[38] = "1000000"
        assert not fix_ns.match(
            actual, expected, description="Failing str/int comparison"
        )

        # Change the type to a float. The match should still fail because of
        # the type difference, despite the numeric values being equal.
        actual[38] = 1000000.0
        assert not fix_ns.match(
            actual, expected, description="Failing float/int comparison"
        )

    def test_mixed_fixmatch(self, fix_ns):
        """Test FIX matches between typed and untyped FIX messages."""
        expected = testing.FixMessage(
            ((35, "D"), (38, "1000000"), (44, "125.83")), typed_values=False
        )
        actual = testing.FixMessage(
            ((35, "D"), (38, "1000000"), (44, 125.83)), typed_values=True
        )

        assert fix_ns.match(actual, expected, description="Mixed FIX match")

    def test_report_modes(self, fix_ns):
        """Test controlling report modes for FIX match."""
        expected = testing.FixMessage((i, (25 * i) - 4) for i in range(10))
        actual = expected.copy()
        expected["wrong"] = "expected"
        actual["wrong"] = "actual"

        assert not fix_ns.match(
            actual, expected, description="Keep all comparisons by default"
        )
        assert len(fix_ns.result.entries) == 1
        dict_assert = fix_ns.result.entries.popleft()
        assert len(dict_assert.comparison) == 11

        assert fix_ns.match(
            actual,
            expected,
            description="Keep ignored comparisons",
            include_tags=[0, 1, 2],
        )

        assert len(fix_ns.result.entries) == 1
        dict_assert = fix_ns.result.entries.popleft()
        assert len(dict_assert.comparison) == 11

        assert fix_ns.match(
            actual,
            expected,
            description="Discard ignored comparisons",
            include_tags=[0, 1, 2],
            report_mode=comparison.ReportOptions.NO_IGNORED,
        )

        assert len(fix_ns.result.entries) == 1
        dict_assert = fix_ns.result.entries.popleft()
        assert len(dict_assert.comparison) == 3

        assert not fix_ns.match(
            actual,
            expected,
            report_mode=comparison.ReportOptions.FAILS_ONLY,
            description="Discard passing comparisons",
        )
        assert len(fix_ns.result.entries) == 1
        dict_assert = fix_ns.result.entries.popleft()
        assert len(dict_assert.comparison) == 1

    def test_flattened_comparison_result(self, fix_ns):
        """Test the comparison result in flattened entries."""
        expected = {
            8: "FIX42",
            9: re.compile(r"[A-Za-z]{2}"),
            555: [
                {
                    600: "A",
                    601: "B",
                    687: [
                        {688: "opq", 689: "rst"},
                        {688: "uvw", 689: "xyz"},
                    ],
                }
            ],
        }
        actual = expected.copy()
        actual[9] = "AE"
        actual[555] = [{600: "A", 601: "C", 700: "D"}]
        assert not fix_ns.match(
            actual,
            expected,
            description="complex fix message comparison",
            include_tags=[9, 555, 600, 687],
        )
        assert len(fix_ns.result.entries) == 1

        # Comparison result is a list of list items in below format:
        # [indent, key, result, (act_type, act_value), (exp_type, exp_value)]
        comp_result = fix_ns.result.entries[0].comparison
        _8 = [item for item in comp_result if item[1] == 8][0]
        assert _8[0] == 0 and _8[2][0].lower() == comparison.Match.IGNORED
        _9 = [item for item in comp_result if item[1] == 9][0]
        assert (
            _9[0] == 0
            and _9[2][0].lower() == comparison.Match.PASS
            and _9[4][0] == "REGEX"
        )
        _555 = [item for item in comp_result if item[1] == 555][0]
        assert _555[0] == 0 and _555[2][0].lower() == comparison.Match.FAIL
        _600 = [item for item in comp_result if item[1] == 600][0]
        assert _600[0] == 1 and _600[2][0].lower() == comparison.Match.PASS
        _601 = [item for item in comp_result if item[1] == 601][0]
        assert _601[0] == 1 and _601[2][0].lower() == comparison.Match.IGNORED
        _687 = [item for item in comp_result if item[1] == 687][0]
        assert (
            _687[0] == 1
            and _687[2][0].lower() == comparison.Match.FAIL
            and _687[3] == (None, "ABSENT")  # key not found in actual data
        )
        _688_1, _688_2 = [item for item in comp_result if item[1] == 688]
        assert _688_1[0] == 2 and _688_1[2][0].lower() == comparison.Match.FAIL
        assert _688_2[0] == 2 and _688_2[2][0].lower() == comparison.Match.FAIL
        _689_1, _689_2 = [item for item in comp_result if item[1] == 689]
        assert _689_1[0] == 2 and _689_1[2][0].lower() == comparison.Match.FAIL
        assert _689_2[0] == 2 and _689_2[2][0].lower() == comparison.Match.FAIL
        _700 = [item for item in comp_result if item[1] == 700][0]
        assert (
            _700[0] == 1
            and _700[2][0].lower() == comparison.Match.IGNORED
            and _700[4] == (None, "ABSENT")  # key not found in expected data
        )


class TestResultBaseNamespace(object):
    """Test assertions and other methods in the base result.* namespace."""

    def test_graph_assertion(self):
        """Unit testcase for the result.graph method."""
        result = result_mod.Result()
        graph_assertion = result.graph(
            "Line",
            {
                "Data Name": [
                    {"x": 0, "y": 8},
                    {"x": 1, "y": 5},
                    {"x": 2, "y": 4},
                    {"x": 3, "y": 9},
                    {"x": 4, "y": 1},
                    {"x": 5, "y": 7},
                    {"x": 6, "y": 6},
                    {"x": 7, "y": 3},
                    {"x": 8, "y": 2},
                    {"x": 9, "y": 0},
                ]
            },
            description="Line Graph",
            series_options={"Data Name": {"colour": "red"}},
            graph_options=None,
        )

        assert bool(graph_assertion) is True
        assert len(result.entries) == 1
        assert result.entries[0].graph_type is "Line"
        assert type(result.entries[0].graph_data) is dict
        assert type(result.entries[0].series_options) is dict
        assert result.entries[0].graph_options is None

    def test_attach(self, tmpdir):
        """UT for result.attach method."""
        tmpfile = str(tmpdir.join("attach_me.txt"))
        with open(tmpfile, "w") as f:
            f.write("testplan\n" * 1000)

        result = result_mod.Result(_scratch=str(tmpdir))
        hash = path_utils.hash_file(tmpfile)

        assert result.attach(tmpfile, description="Attach a text file")
        assert len(result.entries) == 1
        attachment_entry = result.entries[0]

        assert attachment_entry.source_path == os.path.join(
            os.path.dirname(tmpfile), attachment_entry.dst_path
        )
        assert hash in attachment_entry.dst_path
        assert attachment_entry.orig_filename == "attach_me.txt"
        assert attachment_entry.filesize == os.path.getsize(tmpfile)

        # The expected destination path depends on the exact hash and filesize
        # of the file we wrote.
        expected_dst_path = "attach_me-{hash}-{filesize}.txt".format(
            hash=hash, filesize=attachment_entry.filesize
        )
        assert attachment_entry.dst_path == expected_dst_path

    def test_attach_in_result_group(self, tmpdir):
        """UT for result.attach method."""
        tmpfile = str(tmpdir.join("attach_me.txt"))
        with open(tmpfile, "w") as f:
            f.write("testplan\n" * 1000)

        size = os.path.getsize(tmpfile)
        description = "Attach a text file at level: {}"

        result = result_mod.Result(_scratch=str(tmpdir))

        assert result.attach(tmpfile, description=description.format(0))
        assert len(result.entries) == 1

        with result.group("subgroup") as subgroup:
            assert subgroup.attach(tmpfile, description=description.format(1))
            assert len(subgroup.entries) == 1

            with subgroup.group("subgroup") as subsubgroup:
                assert subsubgroup.attach(
                    tmpfile, description=description.format(2)
                )
                assert len(subsubgroup.entries) == 1

            assert len(subgroup.entries) == 2
            assert len(subgroup.attachments) == 2
        assert len(result.entries) == 2
        assert len(result.attachments) == 3

        for idx, attachment in enumerate(result.attachments):
            assert attachment.source_path == os.path.join(
                os.path.dirname(tmpfile), attachment.dst_path
            )
            assert attachment.orig_filename == "attach_me.txt"
            assert attachment.filesize == size
            assert attachment.description == description.format(idx)

    def test_matplot(self, tmpdir):
        result_dir = str(tmpdir)
        result = result_mod.Result(_scratch=result_dir)

        x = range(0, 10)
        y = range(0, 10)
        plot.plot(x, y)

        result.matplot(plot, width=4, height=4, description="Matplot")

        assert len(result.entries) == 1
        assert len(result.attachments) == 1

        with result.group(description="subgroup") as subgroup:
            x = range(0, 10)
            y = range(0, 10)
            plot.plot(x, y)

            subgroup.matplot(plot, width=3, height=3, description="Matplot")

        assert len(result.entries) == 2
        assert len(result.attachments) == 2

        # two different file, with same content on the same directory
        assert (
            result.attachments[0].source_path
            != result.attachments[1].source_path
        )
        assert result.attachments[0].filesize > result.attachments[1].filesize
        assert result.attachments[0].source_path.startswith(result_dir)
        assert result.attachments[1].source_path.startswith(result_dir)

    def test_attach_dir(self, tmpdir):
        """UT for result.attach method."""
        path_utils.makeemptydirs(str(tmpdir.join("subdir")))

        tmpfile1 = str(tmpdir.join("1.txt"))
        with open(tmpfile1, "w") as f:
            f.write("testplan\n" * 10)

        tmpfile2 = str(tmpdir.join("2.txt"))
        with open(tmpfile2, "w") as f:
            f.write("testplan\n")

        tmpfile3 = str(tmpdir.join("subdir").join("3.txt"))
        with open(tmpfile3, "w") as f:
            f.write("testplan\n" * 100)

        tmpfile4 = str(tmpdir.join("subdir").join("4.txt"))
        with open(tmpfile4, "w") as f:
            f.write("testplan\n" * 1000)

        result = result_mod.Result()

        assert result.attach(str(tmpdir), description="Attach a directory")
        assert len(result.entries) == 1
        directory_entry = result.entries[0]

        assert directory_entry.source_path == str(tmpdir)
        assert (
            directory_entry.dst_path
            == hashlib.md5(
                directory_entry.source_path.encode("utf-8")
            ).hexdigest()
        )
        assert sorted(directory_entry.file_list) == ["1.txt", "2.txt"]

        assert result.attach(
            str(tmpdir),
            description="Attach a directory with filters",
            ignore=["2.*"],
            only=["*.txt"],
            recursive=True,
        )
        assert len(result.entries) == 2
        directory_entry = result.entries[1]

        assert directory_entry.source_path == str(tmpdir)
        assert (
            directory_entry.dst_path
            == hashlib.md5(
                directory_entry.source_path.encode("utf-8")
            ).hexdigest()
        )
        assert sorted(directory_entry.file_list) == [
            "1.txt",
            "subdir/3.txt",
            "subdir/4.txt",
        ]
