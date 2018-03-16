import logging

import pytest
from schema import SchemaError

from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.testing.multitest.base import Categories
from testplan.testing.multitest.parametrization import (
    ParametrizationError, MAX_METHOD_NAME_LENGTH
)

from testplan import Testplan
from testplan.common.utils.testing import check_report, warnings_suppressed
from testplan.report.testing import TestReport, TestGroupReport, TestCaseReport


LOGGER = logging.getLogger()


def check_parametrization(suite_kls, parametrization_group):

    multitest = MultiTest(
        name='MyMultitest', suites=[suite_kls()])

    plan = Testplan(name='plan', parse_cmdline=False)
    plan.add(multitest)

    plan.run()

    expected_report = TestReport(
        name='plan',
        entries=[
            TestGroupReport(
                name='MyMultitest',
                category=Categories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name='MySuite',
                        category=Categories.SUITE,
                        entries=[parametrization_group]
                    )
                ]
            )
        ]

    )

    check_report(expected_report, plan.report)


def test_basic_parametrization():

    @testsuite
    class MySuite(object):

        @testcase(
            parameters=(
                (1, 2, 3),
                -1,
                (5, -5),
                {'a': 3, 'expected': 4}
            )
        )
        def test_add(self, env, result, a, b=1, expected=0):
            """Simple docstring"""
            result.equal(a + b, expected)

    parametrization_group = TestGroupReport(
        name='test_add',
        description="Simple docstring",
        category=Categories.PARAMETRIZATION,
        entries=[
            TestCaseReport(
                name='test_add__a_1__b_2__expected_3',
                entries=[
                    {
                        'type': 'Equal',
                        'first': 3,
                        'second': 3,
                    }
                ]
            ),
            TestCaseReport(
                name='test_add__0',
                entries=[
                    {
                        'type': 'Equal',
                        'first': 0,
                        'second': 0,
                    }
                ]
            ),
            TestCaseReport(
                name='test_add__1',
                entries=[
                    {
                        'type': 'Equal',
                        'first': 0,
                        'second': 0,
                    }
                ]
            ),
            TestCaseReport(
                name='test_add__a_3__b_1__expected_4',
                entries=[
                    {
                        'type': 'Equal',
                        'first': 4,
                        'second': 4,
                    }
                ]
            ),
        ]
    )

    check_parametrization(MySuite, parametrization_group)


def test_combinatorial_parametrization():

    @testsuite
    class MySuite(object):

        @testcase(
            parameters={
                'a': [1, 2],
                'b': ('alpha', 'beta'),
            }
        )
        def test_sample(self, env, result, a, b):
            result.true(True, '{} - {}'.format(a, b))

    parametrization_group = TestGroupReport(
        name='test_sample',
        category=Categories.PARAMETRIZATION,
        entries=[
            TestCaseReport(
                name='test_sample__a_1__b_alpha',
                entries=[
                    {
                        'type': 'IsTrue',
                        'description': '1 - alpha'
                    }
                ]
            ),
            TestCaseReport(
                name='test_sample__a_1__b_beta',
                entries=[
                    {
                        'type': 'IsTrue',
                        'description': '1 - beta'
                    }
                ]
            ),
            TestCaseReport(
                name='test_sample__a_2__b_alpha',
                entries=[
                    {
                        'type': 'IsTrue',
                        'description': '2 - alpha'
                    }
                ]
            ),
            TestCaseReport(
                name='test_sample__a_2__b_beta',
                entries=[
                    {
                        'type': 'IsTrue',
                        'description': '2 - beta'
                    }
                ]
            ),
        ]
    )

    check_parametrization(MySuite, parametrization_group)


@pytest.mark.parametrize(
    'val, msg',
    (
        (
            [(1, 2, 3, 4)],
            'Should fail if tuple length is longer than args.'
        ),
        (
            1,
            'Should fail if shortcut notation is used while the testcase'
            'accepts multiple parametrization arguments.'
        ),
        (
            [(1,)],
            'Should fail if tuple is missing values for required args.'
        ),
        (
            tuple(),
            'Should fail for empty tuple / list (basic parametrization).'
        ),
        (
            [{'a': 1, 'b': 2, 'e': 3}],
            'Should fail if explicit value dict (tuple element) has extra keys.'
        ),
        (
            {},
            'Should fail for empty dict (combinatorial parametrization).'
        ),
        (
            {'a': [1, 2], 'b': 3},
            'Should fail combinatorial parametrization'
            ' for non-iterable dict values.'
        ),
        (
            {'a': [1, 2], 'b': {'foo': 'bar'}},
            'Should fail combinatorial parametrization'
            ' for dicts as dict values.'
        ),
        (
            {'a': [2], 'c': [5]},
            'Should fail combinatorial parametrization'
            ' for missing dict keys for required args.'
        ),
        (
            {'a': [2], 'b': [4], 'e': [12]},
            'Should fail if combinatorial dict has extra keys.'
        ),
    )
)
def test_invalid_parametrization(val, msg):

    LOGGER.info(msg)

    with pytest.raises(ParametrizationError):
        @testsuite
        class MySuite(object):

            @testcase(parameters=val)
            def sample_test(self, env, result, a, b, c=3):
                pass


def test_custom_name_func():
    """`name_func` should be used for generating method names."""
    @testsuite
    class MySuite(object):

        @testcase(
            parameters=(('foo', 'bar'), ('alpha', 'beta')),
            name_func=lambda func_name, kwargs: 'XXX_{a}_{b}_XXX'.format(**kwargs)
        )
        def sample_test(self, env, result, a, b):
            pass

    parametrization_group = TestGroupReport(
        name='sample_test',
        category=Categories.PARAMETRIZATION,
        entries=[
            TestCaseReport(name='XXX_foo_bar_XXX'),
            TestCaseReport(name='XXX_alpha_beta_XXX'),
        ]
    )

    check_parametrization(MySuite, parametrization_group)


@pytest.mark.parametrize(
    'name_func, testcase_names, msg',
    (
        (
            lambda func_name, kwargs: 'same_method',
            ['same_method__0', 'same_method__1'],
            'Should use index fallback if generated names are not unique.'
        ),
        (
            lambda func_name, kwargs: '#@)$*@#%_{a}_{b}',
            ['sample_test__0', 'sample_test__1'],
            'Should use original method_name + index fallback if'
            ' generated names are not valid Python attribute names.'
        ),
        (
            lambda func_name, kwargs: 'a' * (MAX_METHOD_NAME_LENGTH + 1),
            ['sample_test__0', 'sample_test__1'],
            'Should use original method_name + index fallback if generated'
            ' names are longer than {} characters.'.format(
                MAX_METHOD_NAME_LENGTH)
        )
    )
)
def test_name_func_fallback(name_func, testcase_names, msg):

    LOGGER.info(msg)

    with warnings_suppressed():
        @testsuite
        class MySuite(object):

            @testcase(
                parameters=(
                    'alpha',
                    'beta',
                ),
                name_func=name_func
            )
            def sample_test(self, env, result, foo):
                pass

    name_alpha, name_beta = testcase_names
    parametrization_group = TestGroupReport(
        name='sample_test',
        category=Categories.PARAMETRIZATION,
        entries=[
            TestCaseReport(name=name_alpha),
            TestCaseReport(name=name_beta),
        ]
    )

    check_parametrization(MySuite, parametrization_group)


@pytest.mark.parametrize(
    'name_func, msg',
    (
        (
            5,
            'Should fail if name_func is not a callable.',
        ),
        (
            lambda foo, bar: '',
            'Should fail if name_func arg names'
            ' does not match func_name, kwargs.'
        ),
        (
            lambda func_name, kwargs, foo: '',
            'Should fail if name_func arg names do not accept 2 arguments.'
        )
    )
)
def test_invalid_name_func(name_func, msg):

    LOGGER.info(msg)

    with pytest.raises(ParametrizationError):
        @testsuite
        class MySuite(object):

            @testcase(
                parameters=(1, 2),
                name_func=name_func
            )
            def sample_test(self, env, result, a):
                pass


def test_custom_wrapper():
    """Custom wrappers should be applied to each generated testcase."""
    def add_label(value):
        def wrapper(func):
            func.label = value
            return func
        return wrapper

    @testsuite
    class MySuite(object):

        @testcase(
            parameters=((1, 2, 3), (3, 3, 6)),
            custom_wrappers=add_label('foo'),
        )
        def adder_test(self, env, result, a, b, expected):
            result.equal(expected)(a + b)

    assert MySuite.adder_test__a_1__b_2__expected_3.label == 'foo'
    assert MySuite.adder_test__a_3__b_3__expected_6.label == 'foo'


@pytest.mark.parametrize(
    'tag_func, expected_tags',
    (
        (
            lambda kwargs: kwargs['product'],
            {'simple': frozenset(['foo', 'productA'])},
        ),
        (
            lambda kwargs: {'product': kwargs['product']},
            {
                'product': frozenset(['productA']),
                'simple': frozenset(['foo'])
            }
        )
    )
)
def test_tag_func(tag_func, expected_tags):

    @testsuite
    class MySuite(object):

        @testcase(
            parameters=(
                dict(product='productA', category='dummy-category'),
            ),
            tags='foo',
            tag_func=tag_func,
            name_func=lambda func_name, kwargs: 'dummy_name'
        )
        def adder_test(self, env, result, product, category):
            pass
    assert MySuite.dummy_name.tags == expected_tags


@pytest.mark.parametrize(
    'docstring_func, expected_docstring',
    (
        (None, None),  # by default generated testcases have no docstring
        (lambda docstring, kwargs: 'foo', 'foo'),
        (
            lambda docstring, kwargs: '{docstring} '
                                      '- {first} - {second}'.format(
                docstring=docstring, **kwargs),
            'Original docstring - foo - bar'
        )
    )
)
def test_docstring_func(docstring_func, expected_docstring):
    @testsuite
    class DummySuite(object):

        @testcase(
            parameters=(
                    ('foo', 'bar'),
            ),
            name_func=lambda func_name, kwargs: 'dummy_name',
            docstring_func=docstring_func,
        )
        def adder_test(self, env, result, first, second):
            """Original docstring"""
            pass

    assert DummySuite.dummy_name.__doc__ == expected_docstring


def test_parametrization_tagging():
    """
        Parametrization report group should include tags
        generated by `tag_func` and native suite tags in `tag_index` attribute.
    """

    @testsuite(tags='foo')
    class DummySuite(object):

        @testcase(
            parameters=('red', 'blue', 'green'),
            tags='alpha',
            tag_func=lambda kwargs: {'color': kwargs['color']}
        )
        def dummy_test(self, env, result, color):
            pass


    all_tags_index = {
        'simple': frozenset({'foo', 'alpha'}),
        'color': frozenset({'red', 'blue', 'green'})
    }

    parametrization_group = TestGroupReport(
        name='dummy_test',
        category=Categories.PARAMETRIZATION,
        tags={
            'simple': frozenset({'alpha'}),
        },
        tags_index=all_tags_index,
        entries=[
            TestCaseReport(
                name='dummy_test__color_red',
                tags={
                    'simple': frozenset({'alpha'}),
                    'color': frozenset({'red'})
                },
                tags_index={
                    'simple': frozenset({'foo', 'alpha'}),
                    'color': frozenset({'red'})
                }
            ),
            TestCaseReport(
                name='dummy_test__color_blue',
                tags={
                    'simple': frozenset({'alpha'}),
                    'color': frozenset({'blue'})
                },
                tags_index={
                    'simple': frozenset({'foo', 'alpha'}),
                    'color': frozenset({'blue'})
                }
            ),
            TestCaseReport(
                name='dummy_test__color_green',
                tags={
                    'simple': frozenset({'alpha'}),
                    'color': frozenset({'green'})
                },
                tags_index={
                    'simple': frozenset({'foo', 'alpha'}),
                    'color': frozenset({'green'})
                }
            ),
        ]
    )

    multitest = MultiTest(
        name='MyMultitest', suites=[DummySuite()])

    plan = Testplan(name='plan', parse_cmdline=False)
    plan.add(multitest)

    plan.run()

    expected_report = TestReport(
        name='plan',
        entries=[
            TestGroupReport(
                name='MyMultitest',
                tags_index=all_tags_index,
                category=Categories.MULTITEST,
                entries=[
                    TestGroupReport(
                        name='DummySuite',
                        tags={'simple': frozenset({'foo'})},
                        tags_index=all_tags_index,
                        category=Categories.SUITE,
                        entries=[parametrization_group]
                    )
                ]
            )
        ]

    )

    check_report(expected_report, plan.report)


def test_same_name_func():
    """`name_func` should be used for generating method names."""
    @testsuite
    class MySuite(object):

        @testcase(
            parameters=(('foo', 'bar'), ('alpha', 'beta')),
            name_func=lambda func_name, kwargs: 'same_name'
        )
        def sample_test(self, env, result, a, b):
            pass

        @testcase(
            parameters=(('foo', 'bar'), ('alpha', 'beta')),
            name_func=lambda func_name, kwargs: 'same_name'
        )
        def other_test(self, env, result, a, b):
            pass

    with pytest.raises(SchemaError):
        MultiTest(name='abc', suites=[MySuite()])
