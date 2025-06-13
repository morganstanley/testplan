import collections
import decimal
import fractions
import os
import re
import traceback

import pytest

from testplan.common.utils.table import TableEntry
from testplan.testing.multitest.entries import assertions


def multiline(*strings, **kwargs):
    """
    Regex module just takes newline character `\n` into account, but not
    carriage return. So we don't use `os.linesep` here as
    default for basic regex matching.
    """
    line_sep = kwargs.pop("line_sep", "\n")
    return line_sep.join(strings)


class TestAssertion:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("foo", True),
            (True, True),
            (False, False),
            ("", False),
            ([], False),
            (None, False),
        ],
    )
    def test_evaluate(self, value, expected):
        """
        Boolean casted result of evaluate should be
        used for truthiness of an assertion.
        """

        class DummyAssertion(assertions.Assertion):
            def evaluate(self):
                return value

        assertion = DummyAssertion()

        assert assertion.passed is bool(value)
        assert bool(DummyAssertion()) is expected


FUNC_PARAM_NAMES = "first,second"
EQUALITY_PARAMS = [
    ("foo", "foo"),
    (decimal.Decimal("1"), 1),
    ([1], [1]),
    ({1, 2}, {1, 2}),
    (123, 123),
    (1000, 10e2),
]

LESS_THAN_PARAMS = [
    (1, 2),
    ("a", "c"),
    (1000, 10e2 + 1),
    ({1, 2, 3}, {1, 2, 3, 4}),
]

GREATER_THAN_PARAMS = [(second, first) for first, second in LESS_THAN_PARAMS]

INEQUALITY_PARAMS = (
    [
        ("foo", "bar"),
        (decimal.Decimal("1.12"), "1.12"),
        ([], [1]),
        ({}, {1, 2}),
        (123, 321),
    ]
    + LESS_THAN_PARAMS
    + GREATER_THAN_PARAMS
)


def generate_function_assertion_test(
    assertion_kls, passing_params, failing_params
):
    class AssertionTest:
        def _test_evaluate(self, first, second, expected):
            assertion = assertion_kls(first, second)
            assert assertion.first is first
            assert assertion.second is second
            assert bool(assertion) is expected

        @pytest.mark.parametrize(FUNC_PARAM_NAMES, passing_params)
        def test_evaluate_true(self, first, second):
            self._test_evaluate(first, second, True)

        @pytest.mark.parametrize(FUNC_PARAM_NAMES, failing_params)
        def test_evaluate_false(self, first, second):
            self._test_evaluate(first, second, False)

    return AssertionTest


TestEqual = generate_function_assertion_test(
    assertion_kls=assertions.Equal,
    passing_params=EQUALITY_PARAMS,
    failing_params=INEQUALITY_PARAMS,
)

TestNotEqual = generate_function_assertion_test(
    assertion_kls=assertions.NotEqual,
    passing_params=INEQUALITY_PARAMS,
    failing_params=EQUALITY_PARAMS,
)

TestLess = generate_function_assertion_test(
    assertion_kls=assertions.Less,
    passing_params=LESS_THAN_PARAMS,
    failing_params=EQUALITY_PARAMS + GREATER_THAN_PARAMS,
)

TestGreater = generate_function_assertion_test(
    assertion_kls=assertions.Greater,
    passing_params=GREATER_THAN_PARAMS,
    failing_params=EQUALITY_PARAMS + LESS_THAN_PARAMS,
)

TestLessEqual = generate_function_assertion_test(
    assertion_kls=assertions.LessEqual,
    passing_params=LESS_THAN_PARAMS + EQUALITY_PARAMS,
    failing_params=GREATER_THAN_PARAMS,
)

TestGreaterEqual = generate_function_assertion_test(
    assertion_kls=assertions.GreaterEqual,
    passing_params=GREATER_THAN_PARAMS + EQUALITY_PARAMS,
    failing_params=LESS_THAN_PARAMS,
)


APPROXIMATE_EQUALITY_ASSERTION_PARAM_NAMES = "first,second,rel_tol,abs_tol"
IS_CLOSE_PARAMS = [
    (0, 0, 0.0, 0.0),
    (499, 500, 0.003, 0.0),
    (1000, 1001.001, 0.001, 0.0),
    (-500, -555.5, 0.1, 55.0),
    (1e9, 9e8, 0.099, 1.0001e8),
    (True, True, 1e-09, 0.0),
    (False, False, 1e-09, 0.0),
    (decimal.Decimal("0.999"), decimal.Decimal("0.9999"), 0, 0.001),
    (
        fractions.Fraction(99, 100),
        fractions.Fraction(100, 101),
        0.00010001,
        0.0,
    ),
    (3 + 4j, 3 + 5j, 0.18, 0.0),
    (3 + 4j, 4 + 3j, 0.0, 1.42),
    (0, 1e100, 0.0, float("inf")),
    (float("inf"), float("inf"), 0.0, 0.0),
    (float("-inf"), float("-inf"), 0.0, 0.0),
]

IS_NOT_CLOSE_PARAMS = [
    (0, 0.0001, 0.0, 0.0),
    (499, 500, 0.001, 0.0),
    (1000, 1001.01, 0.001, 0.0),
    (-500, -555.5, 0.0999, 55.0),
    (1e9, 9e8, 0.099, 0.9999e8),
    (True, False, 1e-09, 0.5),
    (
        decimal.Decimal("0.999"),
        decimal.Decimal("0.9999"),
        decimal.Decimal("0.0009"),
        0.0,
    ),
    (
        fractions.Fraction(99, 100),
        fractions.Fraction(100, 101),
        0.00009999,
        1e-05,
    ),
    (3 + 4j, 3 + 2j, 0.18, 0.0),
    (5 + 4j, 4 + 3j, 0.0, 1.41),
    (float("inf"), float("-inf"), 0.0, float("inf")),
    (float("inf"), 1.0, 0.0, float("inf")),
    (float("nan"), float("inf"), 0.0, float("inf")),
    (float("nan"), 1e12, 0.0, float("inf")),
]


def generate_approximate_equality_assertion_test(
    assertion_kls, passing_params, failing_params
):
    class ApproximateEqualityTest:
        def _test_evaluate(self, first, second, rel_tol, abs_tol, expected):
            assertion = assertion_kls(first, second, rel_tol, abs_tol)
            assert assertion.first is first
            assert assertion.second is second
            assert assertion.rel_tol is rel_tol
            assert assertion.abs_tol is abs_tol
            assert bool(assertion) is expected

        @pytest.mark.parametrize(
            APPROXIMATE_EQUALITY_ASSERTION_PARAM_NAMES, passing_params
        )
        def test_evaluate_true(self, first, second, rel_tol, abs_tol):
            self._test_evaluate(first, second, rel_tol, abs_tol, True)

        @pytest.mark.parametrize(
            APPROXIMATE_EQUALITY_ASSERTION_PARAM_NAMES, failing_params
        )
        def test_evaluate_false(self, first, second, rel_tol, abs_tol):
            self._test_evaluate(first, second, rel_tol, abs_tol, False)

    return ApproximateEqualityTest


TestIsClose = generate_approximate_equality_assertion_test(
    assertion_kls=assertions.IsClose,
    passing_params=IS_CLOSE_PARAMS,
    failing_params=IS_NOT_CLOSE_PARAMS,
)


MEMBERSHIP_PARAM_NAMES = "member,container"
CONTAINS_PARAMS = [
    ("foo", "foobar"),
    ("foo", ["foo", "bar"]),
    ("foo", {"foo", "bar"}),
    ("foo", {"foo": 1, "bar": 2}),
]

NOT_CONTAINS_PARAMS = [
    ("baz", "foobar"),
    ("baz", ["foo", "bar"]),
    ("baz", {"foo", "bar"}),
    ("baz", {"foo": 1, "bar": 2}),
]


def generate_membership_test(assertion_kls, passing_params, failing_params):
    class MembershipTest:
        def _test_evaluate(self, member, container, expected):
            assertion = assertion_kls(member, container)
            assert assertion.member is member
            assert assertion.container is container
            assert bool(assertion) == expected

        @pytest.mark.parametrize(MEMBERSHIP_PARAM_NAMES, passing_params)
        def test_evaluate_true(self, member, container):
            self._test_evaluate(member, container, True)

        @pytest.mark.parametrize(MEMBERSHIP_PARAM_NAMES, failing_params)
        def test_evaluate_false(self, member, container):
            self._test_evaluate(member, container, False)

    return MembershipTest


TestContain = generate_membership_test(
    assertion_kls=assertions.Contain,
    passing_params=CONTAINS_PARAMS,
    failing_params=NOT_CONTAINS_PARAMS,
)

TestNotContain = generate_membership_test(
    assertion_kls=assertions.NotContain,
    passing_params=NOT_CONTAINS_PARAMS,
    failing_params=CONTAINS_PARAMS,
)


REGEX_PARAM_NAMES = "regexp,string,flags,expected_match_indexes"


class BaseRegexTest:
    assertion_class = None

    def _test_evaluate(
        self,
        regexp,
        string,
        expected_match_indexes,
        expected,
        flags=0,
        *args,
        **kwargs,
    ):
        assertion = self.assertion_class(  # pylint: disable=not-callable
            regexp=regexp, string=string, flags=flags, *args, **kwargs
        )
        pattern = regexp if isinstance(regexp, str) else regexp.pattern

        assert assertion.string is string
        assert assertion.pattern is pattern
        assert assertion.match_indexes == expected_match_indexes
        assert bool(assertion) is expected


def generate_regex_test(assertion_kls, passing_params, failing_params):
    class RegexTest(BaseRegexTest):
        assertion_class = assertion_kls

        @pytest.mark.parametrize(REGEX_PARAM_NAMES, passing_params)
        def test_evaluate_true(
            self, regexp, string, flags, expected_match_indexes
        ):
            self._test_evaluate(
                regexp=regexp,
                string=string,
                flags=flags,
                expected_match_indexes=expected_match_indexes,
                expected=True,
            )

        @pytest.mark.parametrize(REGEX_PARAM_NAMES, failing_params)
        def test_evaluate_false(
            self, regexp, string, flags, expected_match_indexes
        ):
            self._test_evaluate(
                regexp=regexp,
                string=string,
                flags=flags,
                expected_match_indexes=expected_match_indexes,
                expected=False,
            )

    return RegexTest


REGEX_MATCH_PASS_PARAMS = [
    ("foo", "foobar", 0, [(0, 3)]),
    (re.compile(r"foo"), "foobar", 0, [(0, 3)]),
    ("hello", "helloworld", re.DOTALL, [(0, 5)]),
]

REGEX_MATCH_FAIL_PARAMS = [
    ("bar", "foobar", 0, []),
    (re.compile(r"bar"), "foobar", 0, []),
    ("bar", "hellobarworld", 0, []),
]


TestRegexMatch = generate_regex_test(
    assertion_kls=assertions.RegexMatch,
    passing_params=REGEX_MATCH_PASS_PARAMS,
    failing_params=REGEX_MATCH_FAIL_PARAMS,
)


TestRegexMatchNotExists = generate_regex_test(
    assertion_kls=assertions.RegexMatchNotExists,
    passing_params=REGEX_MATCH_FAIL_PARAMS,
    failing_params=REGEX_MATCH_PASS_PARAMS,
)


REGEX_SEARCH_PASS_PARAMS = [
    (r"foo", "hello foo world", 0, [(6, 9)]),
    (r"^foo$", multiline("hello", "foo", "world"), re.MULTILINE, [(6, 9)]),
]

REGEX_SEARCH_FAIL_PARAMS = [
    (r"bar", "hello foo world", 0, []),
    (r"^foo$", multiline("hello", "foo", "world"), 0, []),
]


TestRegexSearch = generate_regex_test(
    assertion_kls=assertions.RegexSearch,
    passing_params=REGEX_SEARCH_PASS_PARAMS,
    failing_params=REGEX_SEARCH_FAIL_PARAMS,
)


TestRegexSearchNotExists = generate_regex_test(
    assertion_kls=assertions.RegexSearchNotExists,
    passing_params=REGEX_SEARCH_FAIL_PARAMS,
    failing_params=REGEX_SEARCH_PASS_PARAMS,
)


REGEX_MATCH_LINE_PASS_PARAMS = [
    (re.compile("foo"), "foobarfoo", 0, [(0, 0, 3)]),
    (
        ".*foo",
        multiline("hello", "foobar", "world", "barfoo", line_sep=os.linesep),
        0,
        [(1, 0, 3), (3, 0, 6)],
    ),
    ("foo", multiline("foobar", "baz", line_sep=os.linesep), 0, [(0, 0, 3)]),
]

REGEX_MATCH_LINE_FAIL_PARAMS = [
    (
        "baz",
        multiline("hello", "foobar", "world", "barfoo", line_sep=os.linesep),
        0,
        [],
    ),
    (re.compile("baz"), "foobarfoo", 0, []),
]


TestRegexMatchLine = generate_regex_test(
    assertion_kls=assertions.RegexMatchLine,
    passing_params=REGEX_MATCH_LINE_PASS_PARAMS,
    failing_params=REGEX_MATCH_LINE_FAIL_PARAMS,
)


REGEX_FIND_ITER_PARAM_NAMES = (
    "regexp,string,flags,condition,expected_match_indexes"
)

REGEX_FIND_ITER_PASS_PARAMS = [
    ("foo", "foo bar foo baz", 0, None, [(0, 3), (8, 11)]),
    (
        re.compile(r"foo"),
        "foo bar foo baz",
        0,
        lambda num_matches: num_matches == 2,
        [(0, 3), (8, 11)],
    ),
    (
        "^foo$",
        multiline("hello", "foo", "world", "foo"),
        re.MULTILINE,
        None,
        [(6, 9), (16, 19)],
    ),
]

REGEX_FIND_ITER_FAIL_PARAMS = [
    (
        "foo",
        "foo bar foo baz",
        0,
        lambda num_matches: num_matches > 5,
        [(0, 3), (8, 11)],
    ),
    ("^foo$", multiline("hello", "foo", "world", "foo"), 0, None, []),
    ("bar", "hello world", 0, None, []),
]


class TestRegexFindIter(BaseRegexTest):
    assertion_class = assertions.RegexFindIter

    @pytest.mark.parametrize(
        REGEX_FIND_ITER_PARAM_NAMES, REGEX_FIND_ITER_PASS_PARAMS
    )
    def test_evaluate_true(
        self, regexp, string, flags, condition, expected_match_indexes
    ):
        self._test_evaluate(
            regexp=regexp,
            string=string,
            flags=flags,
            condition=condition,
            expected_match_indexes=expected_match_indexes,
            expected=True,
        )

    @pytest.mark.parametrize(
        REGEX_FIND_ITER_PARAM_NAMES, REGEX_FIND_ITER_FAIL_PARAMS
    )
    def test_evaluate_fail(
        self, regexp, string, flags, condition, expected_match_indexes
    ):
        self._test_evaluate(
            regexp=regexp,
            string=string,
            flags=flags,
            condition=condition,
            expected_match_indexes=expected_match_indexes,
            expected=False,
        )


EQUAL_SLICES_PARAM_NAMES = "actual,expected,slices,expected_data"


def generate_equal_slices_test(assertion_kls, passing_params, failing_params):
    class EqualSlicesTest:
        def _test_evaluate(
            self, actual, expected, slices, expected_data, expected_result
        ):
            assertion = assertion_kls(
                actual=actual, expected=expected, slices=slices
            )

            assert assertion.data == expected_data
            assert bool(assertion) == expected_result

        @pytest.mark.parametrize(EQUAL_SLICES_PARAM_NAMES, passing_params)
        def test_evaluate_true(self, actual, expected, slices, expected_data):
            self._test_evaluate(
                actual=actual,
                expected=expected,
                slices=slices,
                expected_data=expected_data,
                expected_result=True,
            )

        @pytest.mark.parametrize(EQUAL_SLICES_PARAM_NAMES, failing_params)
        def test_evaluate_false(self, actual, expected, slices, expected_data):
            self._test_evaluate(
                actual=actual,
                expected=expected,
                slices=slices,
                expected_data=expected_data,
                expected_result=False,
            )

    return EqualSlicesTest


EQUAL_SLICES_PASS_PARAMS = [
    (
        "abcde",
        "abcxx",
        [slice(0, 3)],
        [
            assertions.SliceComparison(
                slice=slice(0, 3),
                comparison_indices=[0, 1, 2],
                mismatch_indices=[],
                actual="abc",
                expected="abc",
            )
        ],
    ),
    (
        "abcde",
        "abbbe",
        [slice(0, 1), slice(4, 5)],
        [
            assertions.SliceComparison(
                slice=slice(0, 1),
                comparison_indices=[0],
                mismatch_indices=[],
                actual="a",
                expected="a",
            ),
            assertions.SliceComparison(
                slice=slice(4, 5),
                comparison_indices=[4],
                mismatch_indices=[],
                actual="e",
                expected="e",
            ),
        ],
    ),
    (
        [1, 2, 3, 4, 5, 6],
        [1, 2, "a", "b", 5, 6],
        [slice(0, 2), slice(4, 6)],
        [
            assertions.SliceComparison(
                slice=slice(0, 2),
                comparison_indices=[0, 1],
                mismatch_indices=[],
                actual=[1, 2],
                expected=[1, 2],
            ),
            assertions.SliceComparison(
                slice=slice(4, 6),
                comparison_indices=[4, 5],
                mismatch_indices=[],
                actual=[5, 6],
                expected=[5, 6],
            ),
        ],
    ),
]

EQUAL_SLICES_FAIL_PARAMS = [
    (
        "abcde",
        "abcxx",
        [slice(2, 5)],
        [
            assertions.SliceComparison(
                slice=slice(2, 5),
                comparison_indices=[2, 3, 4],
                mismatch_indices=[3, 4],
                actual="cde",
                expected="cxx",
            )
        ],
    ),
    # fails for different lengths, this may change
    ("abcde", "abcdef", [slice(0, 5)], []),
    (
        [1, 2, 3, 4, 5],
        [1, 1, 1, 1, 5],
        [slice(1, 4)],
        [
            assertions.SliceComparison(
                slice=slice(1, 4),
                comparison_indices=[1, 2, 3],
                mismatch_indices=[1, 2, 3],
                actual=[2, 3, 4],
                expected=[1, 1, 1],
            )
        ],
    ),
]


TestEqualSlices = generate_equal_slices_test(
    assertion_kls=assertions.EqualSlices,
    passing_params=EQUAL_SLICES_PASS_PARAMS,
    failing_params=EQUAL_SLICES_FAIL_PARAMS,
)


EQUAL_EXCLUDE_SLICES_PASS_PARAMS = [
    (
        "abcde",
        "abcxx",
        [slice(3, 5)],
        [
            assertions.SliceComparison(
                slice=slice(3, 5),
                comparison_indices=[0, 1, 2],
                mismatch_indices=[],
                actual="abc",
                expected="abc",
            )
        ],
    ),
    (
        "abcde",
        "abbbe",
        [slice(1, 2), slice(2, 3), slice(3, 4)],
        [
            assertions.SliceComparison(
                slice=slice(1, 2),
                comparison_indices=[0, 2, 3, 4],
                mismatch_indices=[2, 3],
                actual="acde",
                expected="abbe",
            ),
            assertions.SliceComparison(
                slice=slice(2, 3),
                comparison_indices=[0, 1, 3, 4],
                mismatch_indices=[3],
                actual="abde",
                expected="abbe",
            ),
            assertions.SliceComparison(
                slice=slice(3, 4),
                comparison_indices=[0, 1, 2, 4],
                mismatch_indices=[2],
                actual="abce",
                expected="abbe",
            ),
        ],
    ),
    (
        [1, 2, 3, 4, 5, 6],
        [1, 2, "a", "b", 5, 6],
        [slice(2, 4)],
        [
            assertions.SliceComparison(
                slice=slice(2, 4),
                comparison_indices=[0, 1, 4, 5],
                mismatch_indices=[],
                actual=[1, 2, 5, 6],
                expected=[1, 2, 5, 6],
            )
        ],
    ),
]

EQUAL_EXCLUDE_SLICES_FAIL_PARAMS = [
    (
        "abcde",
        "abcxx",
        [slice(2, 4)],
        [
            assertions.SliceComparison(
                slice=slice(2, 4),
                comparison_indices=[0, 1, 4],
                mismatch_indices=[4],
                actual="abe",
                expected="abx",
            )
        ],
    ),
    # fails for different lengths, this may change
    ("axxxe", "axxxef", [slice(1, 4)], []),
    (
        [1, 2, 3, 4, 5],
        [1, 1, 1, 1, 5],
        [slice(1, 2)],
        [
            assertions.SliceComparison(
                slice=slice(1, 2),
                comparison_indices=[0, 2, 3, 4],
                mismatch_indices=[2, 3],
                actual=[1, 3, 4, 5],
                expected=[1, 1, 1, 5],
            )
        ],
    ),
]


TestEqualExcludeSlices = generate_equal_slices_test(
    assertion_kls=assertions.EqualExcludeSlices,
    passing_params=EQUAL_EXCLUDE_SLICES_PASS_PARAMS,
    failing_params=EQUAL_EXCLUDE_SLICES_FAIL_PARAMS,
)


EXCEPTION_RAISED_PARAM_NAMES = (
    "raised_exception,expected_exceptions,pattern,func"
)

EXCEPTION_RAISED_PASS_PARAMS = [
    (TypeError(), [ValueError, TypeError], None, None),
    (TypeError("foo"), [ValueError, TypeError], "foo", None),
    (TypeError("foo"), [ValueError, TypeError], None, lambda exc: True),
    (NotImplementedError(), [Exception], None, None),
]

EXCEPTION_RAISED_FAIL_PARAMS = [
    (Exception(), [ValueError, TypeError], None, None),
    (TypeError("foo"), [ValueError, TypeError], "bar", None),
    (TypeError("foo"), [ValueError, TypeError], None, lambda exc: False),
]


def generate_exception_raised_test(
    assertion_kls, passing_params, failing_params
):
    class TestException:
        def _test_evaluate(
            self,
            raised_exception,
            expected_exceptions,
            pattern,
            func,
            expected,
        ):
            assertion = assertion_kls(
                raised_exception=raised_exception,
                expected_exceptions=expected_exceptions,
                pattern=pattern,
                func=func,
            )

            assert assertion.raised_exception is raised_exception
            assert list(assertion.expected_exceptions) == list(
                expected_exceptions
            )
            assert assertion.pattern is pattern
            assert assertion.func is func
            assert bool(assertion) == expected

        @pytest.mark.parametrize(EXCEPTION_RAISED_PARAM_NAMES, passing_params)
        def test_evaluate_true(
            self, raised_exception, expected_exceptions, pattern, func
        ):
            self._test_evaluate(
                raised_exception=raised_exception,
                expected_exceptions=expected_exceptions,
                pattern=pattern,
                func=func,
                expected=True,
            )

        @pytest.mark.parametrize(EXCEPTION_RAISED_PARAM_NAMES, failing_params)
        def test_evaluate_false(
            self, raised_exception, expected_exceptions, pattern, func
        ):
            self._test_evaluate(
                raised_exception=raised_exception,
                expected_exceptions=expected_exceptions,
                pattern=pattern,
                func=func,
                expected=False,
            )

    return TestException


TestExceptionRaised = generate_exception_raised_test(
    assertion_kls=assertions.ExceptionRaised,
    passing_params=EXCEPTION_RAISED_PASS_PARAMS,
    failing_params=EXCEPTION_RAISED_FAIL_PARAMS,
)


TestExceptionNotRaised = generate_exception_raised_test(
    assertion_kls=assertions.ExceptionNotRaised,
    passing_params=EXCEPTION_RAISED_FAIL_PARAMS,
    failing_params=EXCEPTION_RAISED_PASS_PARAMS,
)


DIFF_ASSERTION_PARAM_NAMES = (
    "first,second,ignore_space_change,"
    "ignore_whitespaces,ignore_blank_lines,"
    "unified,context"
)
NO_DIFFERENCE_PARAMS = [
    ("abc\nxyz\n", "abc\nxyz\n", False, False, False, False, False),
    ("abc\r\nxy z\r\n", "abc \nxy\t\tz\n", True, False, False, True, False),
    (" abc\r\nxyz\r\n", "abc \nx y\tz\n", False, True, False, False, True),
    ("abc\n\nxyz\n", "abc\nxyz\n\n", False, False, True, False, False),
    ("abc\nxyz\n", "abc\r\nxyz", False, True, True, True, False),
]

DIFFERENCE_PARAMS = [
    ("abc\nxyz\n", "abcd\nxyz\n", False, False, False, False, False),
    ("abc\nxyz\n", " abc\nxyz\n", True, False, False, True, False),
    (" abc\nxyz\n", "abc\nxyz\n\n", False, True, False, False, True),
    ("abc\nxyz\n", "abc\nxyz\n \n", False, False, True, False, False),
    (" abc\nxyz\n", "abc\nxy z\nuvw\n", True, False, True, True, False),
]


def generate_diff_assertion_test(
    assertion_kls, passing_params, failing_params
):
    class DiffTest:
        def _test_evaluate(
            self,
            first,
            second,
            ignore_space_change,
            ignore_whitespaces,
            ignore_blank_lines,
            unified,
            context,
            expected,
        ):
            assertion = assertion_kls(
                first,
                second,
                ignore_space_change,
                ignore_whitespaces,
                ignore_blank_lines,
                unified,
                context,
            )
            assert "".join(assertion.first) == first
            assert "".join(assertion.second) == second
            assert assertion.ignore_space_change is ignore_space_change
            assert assertion.ignore_whitespaces is ignore_whitespaces
            assert assertion.ignore_blank_lines is ignore_blank_lines
            assert assertion.unified is unified
            assert assertion.context is context
            assert bool(assertion) is expected

        @pytest.mark.parametrize(DIFF_ASSERTION_PARAM_NAMES, passing_params)
        def test_evaluate_true(
            self,
            first,
            second,
            ignore_space_change,
            ignore_whitespaces,
            ignore_blank_lines,
            unified,
            context,
        ):
            self._test_evaluate(
                first=first,
                second=second,
                ignore_space_change=ignore_space_change,
                ignore_whitespaces=ignore_whitespaces,
                ignore_blank_lines=ignore_blank_lines,
                unified=unified,
                context=context,
                expected=True,
            )

        @pytest.mark.parametrize(DIFF_ASSERTION_PARAM_NAMES, failing_params)
        def test_evaluate_false(
            self,
            first,
            second,
            ignore_space_change,
            ignore_whitespaces,
            ignore_blank_lines,
            unified,
            context,
        ):
            self._test_evaluate(
                first=first,
                second=second,
                ignore_space_change=ignore_space_change,
                ignore_whitespaces=ignore_whitespaces,
                ignore_blank_lines=ignore_blank_lines,
                unified=unified,
                context=context,
                expected=False,
            )

    return DiffTest


TestDiff = generate_diff_assertion_test(
    assertion_kls=assertions.LineDiff,
    passing_params=NO_DIFFERENCE_PARAMS,
    failing_params=DIFFERENCE_PARAMS,
)


COLUMN_CONTAIN_PARAM_NAMES = (
    "table,expected_data,values,column,limit,report_fails_only"
)

COLUMN_CONTAIN_PASS_PARAMS = [
    # Scenario 1
    (
        [["name", "age"], ["Bob", 12], ["Kevin", 15], ["Fred", 16]],
        [
            assertions.ColumnContainComparison(0, "Bob", True),
            assertions.ColumnContainComparison(1, "Kevin", True),
            assertions.ColumnContainComparison(2, "Fred", True),
        ],
        ["Bob", "Kevin", "Fred"],
        "name",
        0,
        False,
    ),
    # Scenario 2, empty results because report_fails_only is True
    (
        [["name", "age"], ["Bob", 12], ["Kevin", 15], ["Fred", 16]],
        [],
        ["Bob", "Kevin", "Fred"],
        "name",
        0,
        True,
    ),
    # Scenario 3, subset of original table because limit = 2
    (
        [["name", "age"], ["Bob", 12], ["Kevin", 15], ["Fred", 16]],
        [
            assertions.ColumnContainComparison(0, "Bob", True),
            assertions.ColumnContainComparison(1, "Kevin", True),
        ],
        ["Bob", "Kevin"],
        "name",
        2,
        False,
    ),
]

COLUMN_CONTAIN_FAIL_PARAMS = [
    # Scenario 1
    (
        [["name", "age"], ["Bob", 12], ["Kevin", 15], ["Fred", 16]],
        [
            assertions.ColumnContainComparison(0, "Bob", True),
            assertions.ColumnContainComparison(1, "Kevin", True),
            assertions.ColumnContainComparison(2, "Fred", False),
        ],
        ["Bob", "Kevin"],
        "name",
        0,
        False,
    ),
    # Scenario 2, only displays failures
    (
        [["name", "age"], ["Bob", 12], ["Kevin", 15], ["Fred", 16]],
        [assertions.ColumnContainComparison(2, "Fred", False)],
        ["Bob", "Kevin"],
        "name",
        0,
        True,
    ),
]


def _to_list_of_dicts(table):
    if isinstance(table[0], list):
        header, rows = table[0], table[1:]
        return [dict(zip(header, row)) for row in rows]
    return table


class TestColumnContains:
    def _test_evaluate(
        self,
        table,
        values,
        column,
        limit,
        report_fails_only,
        expected,
        expected_data,
    ):
        assertion = assertions.ColumnContain(
            table=table,
            values=values,
            column=column,
            limit=limit,
            report_fails_only=report_fails_only,
        )

        assert assertion.table == _to_list_of_dicts(table)
        assert assertion.values is values
        assert assertion.column is column
        assert assertion.limit is limit
        assert assertion.report_fails_only is report_fails_only
        assert bool(assertion) == expected
        assert assertion.data == expected_data

    @pytest.mark.parametrize(
        COLUMN_CONTAIN_PARAM_NAMES, COLUMN_CONTAIN_PASS_PARAMS
    )
    def test_evaluate_true(
        self, table, expected_data, values, column, limit, report_fails_only
    ):
        self._test_evaluate(
            table=table,
            values=values,
            column=column,
            limit=limit,
            report_fails_only=report_fails_only,
            expected_data=expected_data,
            expected=True,
        )

    @pytest.mark.parametrize(
        COLUMN_CONTAIN_PARAM_NAMES, COLUMN_CONTAIN_FAIL_PARAMS
    )
    def test_evaluate_false(
        self, table, expected_data, values, column, limit, report_fails_only
    ):
        self._test_evaluate(
            table=table,
            values=values,
            column=column,
            limit=limit,
            report_fails_only=report_fails_only,
            expected_data=expected_data,
            expected=False,
        )


GET_COMPARISON_COLUMNS_PARAM_NAMES = (
    "table_1,table_2,include_columns,exclude_columns,expected"
)
GET_COMPARISON_COLUMNS_PARAMS = [
    # No inclusion/exclusion original table columns are used
    [
        [collections.OrderedDict([("col1", 1), ("col2", 2)])],
        [collections.OrderedDict([("col1", 3), ("col2", 4)])],
        None,
        None,
        ["col1", "col2"],
    ],
    # Inclusion columns are used if they are available in both tables
    [
        [collections.OrderedDict([("col1", 1), ("col2", 2), ("col3", 2)])],
        [collections.OrderedDict([("col1", 3), ("col2", 4), ("col3", 2)])],
        ["col1", "col2"],
        None,
        ["col1", "col2"],
    ],
    # Exclusion columns are used if filtered table columns match
    [
        [
            collections.OrderedDict(
                [("col1", 1), ("col2", 2), ("col3", 2), ("col4", 2)]
            )
        ],
        [
            collections.OrderedDict(
                [("col1", 3), ("col2", 4), ("col4", 2), ("col5", 2)]
            )
        ],
        None,
        ["col2", "col3", "col5"],
        ["col1", "col4"],
    ],
]


COMPARISON_PATTERN = re.compile(r"[a]+")


def is_natural_number(value):
    return isinstance(value, int) and value >= 0


GET_COMPARISON_COLUMNS_ERROR_PARAM_NAMES = (
    "table_1,table_2,include_columns,exclude_columns"
)
GET_COMPARISON_COLUMNS_ERROR_PARAMS = [
    # No inclusion/exclusion, columns do not match
    [
        [collections.OrderedDict([("col1", 1), ("col2", 2)])],
        [collections.OrderedDict([("col1", 3), ("col3", 4)])],
        None,
        None,
    ],
    # Inclusion fails when first table has missing columns
    [
        [collections.OrderedDict([("col1", 1), ("col2", 2)])],
        [collections.OrderedDict([("col1", 3), ("col2", 4), ("col3", 2)])],
        ["col1", "col3"],
        None,
    ],
    # Inclusion fails when second table has missing columns
    [
        [collections.OrderedDict([("col1", 1), ("col2", 2), ("col3", 2)])],
        [collections.OrderedDict([("col1", 3), ("col2", 4)])],
        ["col1", "col3"],
        None,
    ],
    # Exclusion fails when filtered tables have mismatching columns
    [
        [collections.OrderedDict([("col1", 1), ("col2", 2), ("col3", 2)])],
        [collections.OrderedDict([("col1", 3), ("col2", 4), ("col4", 4)])],
        None,
        ["col1"],
    ],
    # Failure when both inclusion & exclusion columns are used
    [
        [collections.OrderedDict([("col1", 1), ("col2", 2), ("col3", 2)])],
        [collections.OrderedDict([("col1", 3), ("col2", 4), ("col3", 4)])],
        ["col2"],
        ["col1"],
    ],
]


COMPARE_ROWS_PARAM_NAMES = (
    "table,expected_table,comparison_columns,display_columns,"
    "strict,fail_limit,report_fails_only,expected_result"
)

COMPARE_ROWS_PARAMS = [
    # Basic match, all columns same
    [
        [{"foo": 1, "bar": 2}, {"foo": 3, "bar": 4}, {"foo": None, "bar": 5}],
        [{"foo": 1, "bar": 2}, {"foo": 3, "bar": 4}, {"foo": None, "bar": 5}],
        ["foo", "bar"],
        ["foo", "bar"],
        True,
        0,
        False,
        (
            True,
            [
                assertions.RowComparison(0, [1, 2], {}, {}, {}),
                assertions.RowComparison(1, [3, 4], {}, {}, {}),
                assertions.RowComparison(2, [None, 5], {}, {}, {}),
            ],
        ),
    ],
    # Basic failure, bar column mismatch
    [
        [{"foo": 1, "bar": 2}, {"foo": 3, "bar": 4}, {"foo": None, "bar": 5}],
        [{"foo": 1, "bar": 2}, {"foo": 3, "bar": 5}, {"foo": 6, "bar": None}],
        ["foo", "bar"],
        ["foo", "bar"],
        True,
        0,
        False,
        (
            False,
            [
                assertions.RowComparison(0, [1, 2], {}, {}, {}),
                assertions.RowComparison(1, [3, 4], {"bar": 5}, {}, {}),
                assertions.RowComparison(
                    2, [None, 5], {"foo": 6, "bar": None}, {}, {}
                ),
            ],
        ),
    ],
    # Match using pattern & custom func, `extra` dict is populated
    [
        [{"foo": "aaa", "bar": 5}],
        [{"foo": COMPARISON_PATTERN, "bar": is_natural_number}],
        ["foo", "bar"],
        ["foo", "bar"],
        True,
        0,
        False,
        (
            True,
            [
                assertions.RowComparison(
                    idx=0,
                    data=["aaa", 5],
                    diff={},
                    errors={},
                    extra={
                        "foo": COMPARISON_PATTERN,
                        "bar": is_natural_number,
                    },
                )
            ],
        ),
    ],
    # Fail using pattern & custom func `diff` dict is populated
    [
        [{"foo": "fff", "bar": "xxx"}],
        [{"foo": COMPARISON_PATTERN, "bar": is_natural_number}],
        ["foo", "bar"],
        ["foo", "bar"],
        True,
        0,
        False,
        (
            False,
            [
                assertions.RowComparison(
                    idx=0,
                    data=["fff", "xxx"],
                    diff={"foo": COMPARISON_PATTERN, "bar": is_natural_number},
                    errors={},
                    extra={},
                )
            ],
        ),
    ],
    # comparison_columns should be used for comparison
    # display_columns should be used for displaying row data
    [
        [
            {"first": 1, "second": 2, "third": 3, "fourth": 4},
            {"first": 5, "second": 6, "third": 7, "fourth": 8},
        ],
        [
            {"first": 1, "second": 2, "third": 333, "fourth": 444},
            {"first": 5, "second": 6, "third": 7, "fourth": 8},
        ],
        ["first", "second"],
        ["first", "second", "fourth"],
        True,
        0,
        False,
        (
            True,
            [
                assertions.RowComparison(
                    idx=0,
                    data=[1, 2, 4],
                    diff={},
                    errors={},
                    extra={"fourth": 444},
                ),
                assertions.RowComparison(
                    idx=1,
                    data=[5, 6, 8],
                    diff={},
                    errors={},
                    extra={"fourth": 8},
                ),
            ],
        ),
    ],
    # When fail_limit is used, the result should
    # at most include the first N failing comparisons
    [
        [
            {"foo": 1, "bar": 2},
            {"foo": 10, "bar": 20},
            {"foo": 100, "bar": 200},
            {"foo": 1000, "bar": 2000},
            {"foo": 10000, "bar": 20000},
        ],
        [
            {"foo": 1, "bar": 2},
            {"foo": 11, "bar": 21},
            {"foo": 101, "bar": 201},
            {"foo": 1001, "bar": 2001},
            {"foo": 10001, "bar": 20001},
        ],
        ["foo", "bar"],
        ["foo", "bar"],
        True,
        3,
        False,
        (
            False,
            [
                assertions.RowComparison(
                    idx=0, data=[1, 2], diff={}, errors={}, extra={}
                ),
                assertions.RowComparison(
                    idx=1,
                    data=[10, 20],
                    diff={"foo": 11, "bar": 21},
                    errors={},
                    extra={},
                ),
                assertions.RowComparison(
                    idx=2,
                    data=[100, 200],
                    diff={"foo": 101, "bar": 201},
                    errors={},
                    extra={},
                ),
                assertions.RowComparison(
                    idx=3,
                    data=[1000, 2000],
                    diff={"foo": 1001, "bar": 2001},
                    errors={},
                    extra={},
                ),
            ],
        ),
    ],
    # When report_fails_only is True, the result should
    # only include the failing comparisons
    [
        [
            {"foo": 1, "bar": 2},
            {"foo": 10, "bar": 20},
            {"foo": 100, "bar": 200},
            {"foo": 1000, "bar": 2000},
            {"foo": 10000, "bar": 20000},
        ],
        [
            {"foo": 1, "bar": 2},
            {"foo": 10, "bar": 20},
            {"foo": 101, "bar": 201},
            {"foo": 1000, "bar": 2000},
            {"foo": 10001, "bar": 20001},
        ],
        ["foo", "bar"],
        ["foo", "bar"],
        True,
        0,
        True,
        (
            False,
            [
                assertions.RowComparison(
                    idx=2,
                    data=[100, 200],
                    diff={"foo": 101, "bar": 201},
                    errors={},
                    extra={},
                ),
                assertions.RowComparison(
                    idx=4,
                    data=[10000, 20000],
                    diff={"foo": 10001, "bar": 20001},
                    errors={},
                    extra={},
                ),
            ],
        ),
    ],
]


TABLEMATCH_COLUMN_NAMES = (
    "table,expected_table,include_columns,exclude_columns,expected_message"
)

TABLEMATCH_PASS_PARAMS = [
    [[{"foo": 1, "bar": 2}], [{"foo": 1, "bar": 2}], None, None, None],
    [[], [], None, None, "Both tables are empty."],
    [[{"foo": 1, "bar": 2}], [{"foo": 1, "bar": 3}], ["foo"], None, None],
    [[{"foo": 1, "bar": 2}], [{"foo": 1, "bar": 3}], None, ["bar"], None],
]

TABLEMATCH_FAIL_PARAMS = [
    [[{"foo": 1, "bar": 2}], [{"foo": 1, "bar": 3}], None, None, None],
    [
        [{"foo": 1, "bar": 2}],
        [{"foo": 1, "bar": 2}, {"foo": 4, "bar": 5}],
        None,
        None,
        (
            "Cannot run comparison on tables with different number "
            "of rows (1 vs 2), make sure tables have the same size."
        ),
    ],
    [[{"foo": 1, "bar": 2}], [{"foo": 1, "bar": 3}], ["bar"], None, None],
    [[{"foo": 1, "bar": 2}], [{"foo": 1, "bar": 3}], None, ["foo"], None],
]


class TestTableMatch:
    @pytest.mark.parametrize(
        GET_COMPARISON_COLUMNS_PARAM_NAMES, GET_COMPARISON_COLUMNS_PARAMS
    )
    def test_get_comparison_columns(
        self, table_1, table_2, include_columns, exclude_columns, expected
    ):
        actual = assertions.get_comparison_columns(
            columns_1=TableEntry(table_1).columns,
            columns_2=TableEntry(table_2).columns,
            include_columns=include_columns,
            exclude_columns=exclude_columns,
        )

        assert list(actual) == expected

    @pytest.mark.parametrize(
        GET_COMPARISON_COLUMNS_ERROR_PARAM_NAMES,
        GET_COMPARISON_COLUMNS_ERROR_PARAMS,
    )
    def test_get_comparison_columns_error(
        self, table_1, table_2, include_columns, exclude_columns
    ):
        with pytest.raises(ValueError):
            assertions.get_comparison_columns(
                columns_1=TableEntry(table_1).columns,
                columns_2=TableEntry(table_2).columns,
                include_columns=include_columns,
                exclude_columns=exclude_columns,
            )

    @pytest.mark.parametrize(COMPARE_ROWS_PARAM_NAMES, COMPARE_ROWS_PARAMS)
    def test_compare_rows(
        self,
        table,
        expected_table,
        comparison_columns,
        display_columns,
        strict,
        fail_limit,
        report_fails_only,
        expected_result,
    ):
        assert (
            assertions.compare_rows(
                table=table,
                expected_table=expected_table,
                comparison_columns=comparison_columns,
                display_columns=display_columns,
                strict=strict,
                fail_limit=fail_limit,
                report_fails_only=report_fails_only,
            )
            == expected_result
        )

    def test_compare_rows_invalid_columns(self):
        """
        Row comparison should raise an error if
        `comparison_columns` is not a subset of `display_columns`
        """
        with pytest.raises(ValueError):
            assertions.compare_rows(
                table=[],
                expected_table=[],
                comparison_columns=["foo", "bar"],
                display_columns=["bar", "baz"],
            )

    def test_compare_rows_error(self):
        """
        Getting exact traceback is not very
        trivial so we have this test separate.
        """
        error_ctx = {}

        def error_func(value):
            try:
                raise Exception("some message")
            except Exception:
                error_ctx["msg"] = traceback.format_exc()
                raise

        table = [{"foo": 1, "bar": 2}]

        expected_table = [{"foo": 1, "bar": error_func}]

        passed, row_comparisons = assertions.compare_rows(
            table=table,
            expected_table=expected_table,
            comparison_columns=["foo", "bar"],
            display_columns=["foo", "bar"],
            strict=True,
            fail_limit=0,
        )

        row_comparison = row_comparisons[0]

        traceback_regex = re.compile(r"raise\s{1}")

        error_orig = row_comparison.errors["bar"]
        error_expected = error_ctx["msg"]

        error_orig = error_orig[traceback_regex.search(error_orig).start() :]
        error_expected = error_expected[
            traceback_regex.search(error_expected).start() :
        ]

        assert passed is False
        assert row_comparison.idx == 0
        assert row_comparison.data == [1, 2]
        assert row_comparison.diff == {}
        assert error_orig == error_expected
        assert row_comparison.extra == {"bar": error_func}

    def _test_evaluate(
        self,
        table,
        expected_table,
        include_columns,
        exclude_columns,
        expected_message,
        expected_result,
    ):
        assertion = assertions.TableMatch(
            table=table,
            expected_table=expected_table,
            include_columns=include_columns,
            exclude_columns=exclude_columns,
        )

        assert bool(assertion) == expected_result
        assert assertion.message == expected_message

    @pytest.mark.parametrize(TABLEMATCH_COLUMN_NAMES, TABLEMATCH_PASS_PARAMS)
    def test_evaluate_true(
        self,
        table,
        expected_table,
        include_columns,
        exclude_columns,
        expected_message,
    ):
        self._test_evaluate(
            table=table,
            expected_table=expected_table,
            include_columns=include_columns,
            exclude_columns=exclude_columns,
            expected_message=expected_message,
            expected_result=True,
        )

    @pytest.mark.parametrize(TABLEMATCH_COLUMN_NAMES, TABLEMATCH_FAIL_PARAMS)
    def test_evaluate_false(
        self,
        table,
        expected_table,
        include_columns,
        exclude_columns,
        expected_message,
    ):
        self._test_evaluate(
            table=table,
            expected_table=expected_table,
            include_columns=include_columns,
            exclude_columns=exclude_columns,
            expected_message=expected_message,
            expected_result=False,
        )


TABLEDIFF_COLUMN_NAMES = TABLEMATCH_COLUMN_NAMES

TABLEDIFF_PASS_PARAMS = TABLEMATCH_PASS_PARAMS

TABLEDIFF_FAIL_PARAMS = TABLEMATCH_FAIL_PARAMS


class TestTableDiff:
    """
    Class `TableDiff` inherits class `TableMatch` and they work in
    a similar way, functions invoked by them are almost the same.
    """

    def _test_evaluate(
        self,
        table,
        expected_table,
        include_columns,
        exclude_columns,
        expected_message,
        expected_result,
    ):
        assertion = assertions.TableDiff(
            table=table,
            expected_table=expected_table,
            include_columns=include_columns,
            exclude_columns=exclude_columns,
        )

        assert bool(assertion) == expected_result
        assert assertion.message == expected_message

    @pytest.mark.parametrize(TABLEDIFF_COLUMN_NAMES, TABLEDIFF_PASS_PARAMS)
    def test_evaluate_true(
        self,
        table,
        expected_table,
        include_columns,
        exclude_columns,
        expected_message,
    ):
        self._test_evaluate(
            table=table,
            expected_table=expected_table,
            include_columns=include_columns,
            exclude_columns=exclude_columns,
            expected_message=expected_message,
            expected_result=True,
        )

    @pytest.mark.parametrize(TABLEDIFF_COLUMN_NAMES, TABLEDIFF_FAIL_PARAMS)
    def test_evaluate_false(
        self,
        table,
        expected_table,
        include_columns,
        exclude_columns,
        expected_message,
    ):
        self._test_evaluate(
            table=table,
            expected_table=expected_table,
            include_columns=include_columns,
            exclude_columns=exclude_columns,
            expected_message=expected_message,
            expected_result=False,
        )


XML_TAG_MATCH_PARAM_NAMES = "element,xpath,tags,namespaces"

XML_TAG_MATCH_PASS_PARAMS = [
    # No tags, but xpath exists
    [
        """
          <Root>
            <Test>Foo</Test>
          </Root>
        """,
        "/Root/Test",
        None,
        None,
    ],
    # Tags match in the given xpath
    [
        """
          <Root>
            <Test>Value1</Test>
            <Test>Value2</Test>
          </Root>
        """,
        "/Root/Test",
        ["Value1", "Value2"],
        None,
    ],
    # Pattern match with namespace
    [
        """
          <SOAP-ENV:Envelope
           xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
            <SOAP-ENV:Header/>
              <SOAP-ENV:Body>
                <ns0:message
                 xmlns:ns0="http://testplan">Hello world!</ns0:message>
              </SOAP-ENV:Body>
          </SOAP-ENV:Envelope>
        """,
        "//*/a:message",
        ["Hello*"],
        {"a": "http://testplan"},
    ],
]


XML_TAG_MATCH_FAIL_PARAMS = [
    # xpath does not exist
    [
        """
          <Root>
            <Test>Foo</Test>
          </Root>
        """,
        "/Root/Bar",
        None,
        None,
    ],
    # Tags do not match
    [
        """
          <Root>
            <Test>Foo</Test>
            <Test>Bar</Test>
          </Root>
        """,
        "/Root/Test",
        ["Value1", "Value2"],
        None,
    ],
    # Namespace does not match
    [
        """
          <SOAP-ENV:Envelope
           xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
            <SOAP-ENV:Header/>
              <SOAP-ENV:Body>
                <ns0:message xmlns:ns0="mismatch-ns">Hello world!</ns0:message>
                <ns0:message xmlns:ns0="http://testplan">Foobar</ns0:message>
              </SOAP-ENV:Body>
          </SOAP-ENV:Envelope>
        """,
        "//*/a:message",
        ["Hello*"],
        {"a": "http://testplan"},
    ],
]


class TestXMLCheck:
    def _test_evaluate(
        self, element, xpath, tags, namespaces, expected_result
    ):
        assertion = assertions.XMLCheck(
            element=element, xpath=xpath, tags=tags, namespaces=namespaces
        )

        assert bool(assertion) == expected_result

    @pytest.mark.parametrize(
        XML_TAG_MATCH_PARAM_NAMES, XML_TAG_MATCH_PASS_PARAMS
    )
    def test_evaluate_true(self, element, xpath, tags, namespaces):
        self._test_evaluate(
            element=element,
            xpath=xpath,
            tags=tags,
            namespaces=namespaces,
            expected_result=True,
        )

    @pytest.mark.parametrize(
        XML_TAG_MATCH_PARAM_NAMES, XML_TAG_MATCH_FAIL_PARAMS
    )
    def test_evaluate_false(self, element, xpath, tags, namespaces):
        self._test_evaluate(
            element=element,
            xpath=xpath,
            tags=tags,
            namespaces=namespaces,
            expected_result=False,
        )


@pytest.mark.parametrize(
    "dictionary,has_keys,absent_keys,expected",
    [
        ({"foo": 1, "bar": 2}, ["foo"], [], True),
        ({"foo": 1, "bar": 2}, [], ["bat"], True),
        ({"foo": 1, "bar": 2}, ["foo"], ["bat"], True),
        ({"foo": 1, "bar": 2, "baz": 10}, ["foo"], ["bat"], True),
        ({"foo": 1, "bar": 2}, [], ["foo"], False),
        ({"foo": 1, "bar": 2}, ["bat"], [], False),
        ({"foo": 1, "bar": 2}, ["bat"], ["foo"], False),
    ],
)
def test_dict_check(dictionary, has_keys, absent_keys, expected):
    assertion = assertions.DictCheck(
        dictionary=dictionary, has_keys=has_keys, absent_keys=absent_keys
    )

    assert bool(assertion) is expected
