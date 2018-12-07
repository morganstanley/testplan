"""TODO."""

import re

import pytest

from testplan.testing.multitest.suite import testcase, testsuite
from testplan.testing.multitest import MultiTest


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

