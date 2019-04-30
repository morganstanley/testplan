"""
    This module contains logic for listing representing test context of a plan.
"""
import os
from enum import Enum
import six

from testplan.common.utils.parser import ArgMixin
from testplan.common.utils.logger import TESTPLAN_LOGGER
from .multitest import MultiTest
from .multitest.suite import get_testsuite_name
from testplan.testing import tagging

INDENT = ' '
MAX_TESTCASES = 25


class BaseLister(object):

    def log_test_info(self, instance):
        output = self.get_output(instance)
        if output:
            TESTPLAN_LOGGER.test_info(output)

    def get_output(self, instance):
        raise NotImplementedError


class ExpandedNameLister(BaseLister):
    """
        Lists names of the items within the test context:

        Sample output:

        MultitestAlpha
            SuiteOne
                testcase_foo
                testcase_bar
            SuiteTwo
                testcase_baz
        MultitestBeta
            ...
    """

    def format_instance(self, instance):
        return instance.name

    def format_suite(self, instance, suite):
        if isinstance(suite, six.string_types):
            return suite
        else:
            return get_testsuite_name(suite)

    def format_testcase(self, instance, suite, testcase):
        if isinstance(testcase, six.string_types):
            return testcase
        else:
            return testcase.__name__

    def get_testcase_outputs(self, instance, suite, testcases):
        result = ''
        for testcase in testcases:
            result += '{}{}{}'.format(
                os.linesep,
                INDENT * 4,
                self.format_testcase(
                    instance=instance,
                    suite=suite,
                    testcase=testcase
                )
            )
        return result

    def get_output(self, instance):
        result = ''
        test_context = instance.test_context

        if not test_context:
            return result

        result += self.format_instance(instance)
        for suite, testcases in test_context:
            suite_output = self.format_suite(instance, suite)
            testcase_outputs = self.get_testcase_outputs(
                instance, suite, testcases)
            if suite_output:
                result += '{}{}{}'.format(
                    os.linesep,
                    INDENT * 2,
                    suite_output
                )
                if testcase_outputs:
                    result += testcase_outputs
        return result


class ExpandedPatternLister(ExpandedNameLister):
    """
        Lists the items in test context in a copy-pasta friendly format
        compatible with `--patterns` and `--tags` arguments.

        Example:

        MultitestAlpha
            MultitestAlpha:SuiteOne --tags color=red
                MultitestAlpha:SuiteOne:testcase_foo
                MultitestAlpha:SuiteOne:testcase_bar  --tags color=blue
            MultitestAlpha:SuiteTwo
                MultitestAlpha:SuiteTwo:testcase_baz
        MultitestBeta
            ...
    """

    def format_instance(self, instance):
        return instance.name

    def apply_tag_label(self, pattern, obj):
        if obj.__tags__:
            return '{}  --tags {}'.format(
                pattern, tagging.tag_label(obj.__tags__))
        return pattern

    def format_suite(self, instance, suite):
        if not isinstance(instance, MultiTest):
            return '{}:{}'.format(instance.name, suite)

        pattern = '{}:{}'.format(instance.name, get_testsuite_name(suite))
        return self.apply_tag_label(pattern, suite)

    def format_testcase(self, instance, suite, testcase):

        if not isinstance(instance, MultiTest):
            return '{}:{}:{}'.format(instance.name, suite, testcase)

        pattern = '{}:{}:{}'.format(
            instance.name, get_testsuite_name(suite), testcase.__name__)
        return self.apply_tag_label(pattern, testcase)


class TrimMixin(object):

    def get_testcase_outputs(self, instance, suite, testcases):
        result = ''
        testcases_to_display = testcases[:MAX_TESTCASES]
        rest_testcases = testcases[MAX_TESTCASES:]

        prefix = '{}{}'.format(os.linesep, INDENT * 4)

        for testcase in testcases_to_display:
            result += '{}{}'.format(prefix, self.format_testcase(
                instance=instance,
                suite=suite,
                testcase=testcase
            ))
        if rest_testcases:
            result += '{}{}'.format(
                prefix,
                '... {} more testcases ...'.format(len(rest_testcases))
            )
        return result


class PatternLister(TrimMixin, ExpandedPatternLister):
    """
        Like test lister, but trims list of
        testcases if they exceed <MAX_TESTCASES>.

        This is useful if the user has generated hundreds of
        testcases via parametrization.
    """


class NameLister(TrimMixin, ExpandedNameLister):
    """Trimmed version of ExpandedNameLister"""


class CountLister(BaseLister):
    """Displays the number of suites and total testcases per test instance."""

    def get_output(self, instance):
        test_context = instance.test_context
        if test_context:
            suites, testcase_lists = zip(*test_context)
            total_testcases = sum(map(len, testcase_lists))
            return '{instance_name}: ({num_suites}' \
                   ' suite{num_suites_plural},' \
                   ' {num_testcases}' \
                   ' testcase{num_testcases_plural})'.format(
                    instance_name=instance.name,
                    num_suites=len(suites),
                    num_suites_plural='s' if len(suites) > 1 else '',
                    num_testcases=total_testcases,
                    num_testcases_plural='s' if total_testcases > 1 else ''
                )
        return ''


class ListingArg(ArgMixin, Enum):

    PATTERN_FULL = ExpandedPatternLister()
    NAME_FULL = ExpandedNameLister()
    COUNT = CountLister()
    PATTERN = PatternLister()
    NAME = NameLister()

    @classmethod
    def get_descriptions(cls):
        name_msg = 'List tests in readable format.'
        pattern_msg = (
            'List tests in `--patterns` / `--tags` compatible format.')
        max_testcases_msg = '\tMax {} testcases per ' \
                            'suite will be displayed'.format(MAX_TESTCASES)
        return {
            cls.PATTERN: '{}{}{}'.format(
                pattern_msg,
                os.linesep,
                max_testcases_msg
            ),
            cls.NAME: '{}{}{}'.format(
                name_msg,
                os.linesep,
                max_testcases_msg
            ),
            cls.PATTERN_FULL: pattern_msg,
            cls.NAME_FULL: name_msg,
            cls.COUNT: 'Lists top level instances and total '
                       'number of suites & testcases per instance.'
        }

