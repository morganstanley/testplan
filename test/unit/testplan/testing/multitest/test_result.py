"""Unit tests for the testplan.testing.multitest.result module."""

import mock
import pytest

from testplan.testing.multitest import result as result_mod
from testplan.testing.multitest.suite import testcase, testsuite
from testplan.testing.multitest import MultiTest
from testplan.common.utils import comparison, testing


@testsuite
class AssertionOrder(object):

    @testcase
    def case(self, env, result):
        summary = result.subresult()
        first = result.subresult()
        second = result.subresult()

        second.true(True, 'AssertionSecond')

        result.true(True, 'AssertionMain1')
        result.true(True, 'AssertionMain2')

        first.true(True, 'AssertionFirst1')
        first.true(True, 'AssertionFirst2')

        summary.append(first)
        result.true(first.passed, 'Report passed so far.')
        if first.passed:
            summary.append(second)

        result.prepend(summary)


def test_assertion_orders():
    mtest = MultiTest(name='AssertionsOrder', suites=[AssertionOrder()])
    mtest.run()

    expected = ['AssertionFirst1', 'AssertionFirst2', 'AssertionSecond',
                'AssertionMain1', 'AssertionMain2', 'Report passed so far.']
    assertions = (entry for entry in mtest.report.flatten()
        if isinstance(entry, dict) and entry['meta_type'] == 'assertion')  # pylint: disable=invalid-sequence-index

    for idx, entry in enumerate(assertions):
        assert entry['description'] == expected[idx]


@pytest.fixture
def dict_ns():
    """Dict namespace with a mocked out result object."""
    mock_result = mock.MagicMock()
    return result_mod.DictNamespace(mock_result)


@pytest.fixture
def fix_ns():
    """FIX namespace with a mocked out result object."""
    mock_result = mock.MagicMock()
    return result_mod.FixNamespace(mock_result)


class TestDictNamespace(object):
    """Unit testcases for the result.DictNamespace class."""

    def test_basic_match(self, dict_ns):
        """
        Test the match method against identical expected and actual dicts.
        """
        expected = {'key': 123}
        actual = expected.copy()

        assert dict_ns.match(
            actual,
            expected,
            description='Basic dictmatch of identical dicts passes')

        assert dict_ns.match(
            actual,
            expected,
            description='Force type-check of values',
            value_cmp_func=comparison.COMPARE_FUNCTIONS['check_types'])

        assert dict_ns.match(
            actual,
            expected,
            description='Convert values to strings before comparing',
            value_cmp_func=comparison.COMPARE_FUNCTIONS['stringify'])

    def test_duck_match(self, dict_ns):
        """
        Test the match method by seting different types that can be compared.
        Due to duck-typing, ints and floats can be equal if they refer to the
        same numeric value - in this case, 123 == 123.0. However if
        type-checking is forced by use of the check_types comparison method
        the assertion will fail.
        """
        expected = {'key': 123}
        actual = {'key': 123.0}

        assert dict_ns.match(
            actual,
            expected,
            description='Dictmatch passes since the numeric values are equal.')

        assert not dict_ns.match(
            actual,
            expected,
            description='Dictmatch fails when type comparison is forced.',
            value_cmp_func=comparison.COMPARE_FUNCTIONS['check_types'])

        assert not dict_ns.match(
            actual,
            expected,
            description='Dictmatch with string conversion fails due to '
                        'different string representations of int/float.',
            value_cmp_func=comparison.COMPARE_FUNCTIONS['stringify'])

    def test_fail_match(self, dict_ns):
        """
        Test the match method for types that do not compare equal - in this
        case, 123 should not match "123".
        """
        expected = {'key': 123}
        actual = {'key': '123'}

        assert not dict_ns.match(
            actual,
            expected,
            description='Dictmatch fails because 123 != "123')

        assert not dict_ns.match(
            actual,
            expected,
            description='Dictmatch fails due to type mismatch',
            value_cmp_func=comparison.COMPARE_FUNCTIONS['check_types'])

        assert dict_ns.match(
            actual,
            expected,
            description='Dictmatch passes when values are converted to strings',
            value_cmp_func=comparison.COMPARE_FUNCTIONS['stringify'])

    def test_custom_match(self, dict_ns):
        """Test a dict match using a user-defined comparison function."""
        expected = {'key': 174.24}
        actual = {'key': 174.87}

        tolerance = 1.0
        def cmp_with_tolerance(lhs, rhs):
            """Check that both values are within a given tolerance range."""
            return abs(lhs - rhs) < tolerance

        assert not dict_ns.match(
            actual,
            expected,
            description='Values are not exactly equal')

        assert dict_ns.match(
            actual,
            expected,
            description='Values are equal within tolerance',
            value_cmp_func=cmp_with_tolerance)


class TestFIXNamespace(object):
    """Unit testcases for the result.FixNamespace class."""

    def test_untyped_fixmatch(self, fix_ns):
        """Test FIX matches between untyped FIX messages."""
        expected = testing.FixMessage(
            ((35, 'D'), (38, '1000000'), (44, '125.83')))
        actual = expected.copy()

        assert fix_ns.match(actual, expected, description='Basic FIX match')

    def test_typed_fixmatch(self, fix_ns):
        """Test FIX matches between typed FIX messages."""
        expected = testing.FixMessage(
            ((35, 'D'), (38, 1000000), (44, 125.83)),
            typed_values=True)
        actual = expected.copy()

        assert fix_ns.match(actual, expected, description='Basic FIX match')

        # Now change the type of the actual 38 key's value to str. The assert
        # should fail since we are performing a typed match.
        actual[38] = '1000000'
        assert not fix_ns.match(
            actual, expected, description='Failing str/int comparison')

        # Change the type to a float. The match should still fail because of
        # the type difference, despite the numeric values being equal.
        actual[38] = 1000000.0
        assert not fix_ns.match(
            actual, expected, description='Failing float/int comparison')

    def test_mixed_fixmatch(self, fix_ns):
        """Test FIX matches between typed and untyped FIX messages."""
        expected = testing.FixMessage(
            ((35, 'D'), (38, '1000000'), (44, '125.83')),
            typed_values=False)
        actual = testing.FixMessage(
            ((35, 'D'), (38, '1000000'), (44, 125.83)),
            typed_values=True)

        assert fix_ns.match(actual, expected, description='Mixed FIX match')
