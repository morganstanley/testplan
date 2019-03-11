import pytest

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import Testplan
from testplan.common.utils.testing import (
    log_propagation_disabled, argv_overridden,
    check_report_context, py_version_data
)
from testplan.common.utils.logger import TESTPLAN_LOGGER
from testplan.testing import ordering


@testsuite
class Alpha(object):

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
class Beta(object):

    @testcase
    def test_ccc(self, env, result):
        pass

    @testcase
    def test_xxx(self, env, result):
        pass

    @testcase
    def test_aaa(self, env, result):
        pass


@pytest.mark.parametrize(
    'sorter, report_ctx',
    (
        # Case 1, noop, original declaration & insertion order
        (
            ordering.NoopSorter(),
            [
                ('Multitest', [
                    ('Beta', ['test_ccc', 'test_xxx', 'test_aaa']),
                    ('Alpha', ['test_ccc', 'test_bbb', 'test_aaa']),
                ]),
            ]
        ),
        # Case 2, alphanumerical
        (
            ordering.AlphanumericSorter(),
            [
                ('Multitest', [
                    ('Alpha', ['test_aaa', 'test_bbb', 'test_ccc']),
                    ('Beta', ['test_aaa', 'test_ccc', 'test_xxx']),
                ]),
            ]
        ),
        # Case 3, shuffle all
        (
            ordering.ShuffleSorter(seed=7),
            [
                (
                    'Multitest',
                    py_version_data(
                        py2=[
                            ('Alpha', ['test_bbb', 'test_aaa', 'test_ccc']),
                            ('Beta', ['test_xxx', 'test_aaa', 'test_ccc']),
                        ],
                        py3=[
                            ('Beta', ['test_aaa', 'test_ccc', 'test_xxx']),
                            ('Alpha', ['test_aaa', 'test_ccc', 'test_bbb']),
                        ],
                    )
                )
            ]
        ),
        # # Case 4, shuffle suites
        (
            ordering.ShuffleSorter(seed=7, shuffle_type='suites'),
            [
                (
                    'Multitest', py_version_data(
                        py2=[
                            ('Alpha', ['test_ccc', 'test_bbb', 'test_aaa']),
                            ('Beta', ['test_ccc', 'test_xxx', 'test_aaa'])
                        ],
                        py3=[
                            ('Beta', ['test_ccc', 'test_xxx', 'test_aaa']),
                            ('Alpha', ['test_ccc', 'test_bbb', 'test_aaa'])
                        ]
                    )
                )
            ]
        ),
        # # Case 5, shuffle testcases
        (
            ordering.ShuffleSorter(seed=7, shuffle_type='testcases'),
            [
                (
                    'Multitest',
                    py_version_data(
                        py2=[
                            ('Beta', ['test_xxx', 'test_aaa', 'test_ccc']),
                            ('Alpha', ['test_bbb', 'test_aaa', 'test_ccc']),
                        ],
                        py3=[
                            ('Beta', ['test_aaa', 'test_ccc', 'test_xxx']),
                            ('Alpha', ['test_aaa', 'test_ccc', 'test_bbb']),
                        ]
                    )
                 )
            ]
        ),
    ),
)
def test_programmatic_ordering(sorter, report_ctx):
    multitest_x = MultiTest(
        name='Multitest', suites=[Beta(), Alpha()])
    plan = Testplan(
        name='plan',
        parse_cmdline=False,
        test_sorter=sorter
    )
    plan.add(multitest_x)

    with log_propagation_disabled(TESTPLAN_LOGGER):
        plan.run()

    test_report = plan.report
    check_report_context(test_report, report_ctx)


@pytest.mark.parametrize(
    'cmdline_args, report_ctx',
    (
        # Case 1, noop
        (
            tuple(),
            [
                ('Multitest', [
                    ('Beta', ['test_ccc', 'test_xxx', 'test_aaa']),
                    ('Alpha', ['test_ccc', 'test_bbb', 'test_aaa']),
                ]),
            ]
        ),
        # Case 2, shuffle all
        (
            ('--shuffle', 'all', '--shuffle-seed', '7'),
            [
                (
                    'Multitest',
                    py_version_data(
                        py2=[
                            ('Alpha', ['test_bbb', 'test_aaa', 'test_ccc']),
                            ('Beta', ['test_xxx', 'test_aaa', 'test_ccc']),
                        ],
                        py3=[
                            ('Beta', ['test_aaa', 'test_ccc', 'test_xxx']),
                            ('Alpha', ['test_aaa', 'test_ccc', 'test_bbb']),
                        ]
                    ),
                )
            ]
        ),
        # Case 3 shuffle suites & testcases
        (
            ('--shuffle', 'suites', 'testcases', '--shuffle-seed', '7'),
            [
                (
                    'Multitest',
                    py_version_data(
                        py2=[
                            ('Alpha', ['test_bbb', 'test_aaa', 'test_ccc']),
                            ('Beta', ['test_xxx', 'test_aaa', 'test_ccc']),
                        ],
                        py3=[
                            ('Beta', ['test_aaa', 'test_ccc', 'test_xxx']),
                            ('Alpha', ['test_aaa', 'test_ccc', 'test_bbb']),
                        ]
                    ),
                )
            ]
        ),
        # Case 4, shuffle suites
        (
            ('--shuffle', 'suites', '--shuffle-seed', '7'),
            [
                (
                    'Multitest',
                    py_version_data(
                        py2=[
                            ('Alpha', ['test_ccc', 'test_bbb', 'test_aaa']),
                            ('Beta', ['test_ccc', 'test_xxx', 'test_aaa']),
                        ],
                        py3=[
                            ('Beta', ['test_ccc', 'test_xxx', 'test_aaa']),
                            ('Alpha', ['test_ccc', 'test_bbb', 'test_aaa']),
                        ]
                    ),
                )
            ]
        ),
        # Case 5, shuffle testcases
        (
            ('--shuffle', 'testcases', '--shuffle-seed', '7'),
            [
                (
                    'Multitest',
                    py_version_data(
                        py2=[
                            ('Beta', ['test_xxx', 'test_aaa', 'test_ccc']),
                            ('Alpha', ['test_bbb', 'test_aaa', 'test_ccc']),
                        ],
                        py3=[
                            ('Beta', ['test_aaa', 'test_ccc', 'test_xxx']),
                            ('Alpha', ['test_aaa', 'test_ccc', 'test_bbb']),
                        ]
                    ),
                )
            ]
        ),
    )
)
def test_command_line_ordering(cmdline_args, report_ctx):

    multitest_x = MultiTest(
        name='Multitest', suites=[Beta(), Alpha()])

    with argv_overridden(*cmdline_args):
        plan = Testplan(name='plan', parse_cmdline=True)
        plan.add(multitest_x)

        with log_propagation_disabled(TESTPLAN_LOGGER):
            plan.run()

    test_report = plan.report
    check_report_context(test_report, report_ctx)
