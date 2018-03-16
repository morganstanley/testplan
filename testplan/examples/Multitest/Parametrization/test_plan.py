"""
This example shows how to use the parametrization
feature of `@testcase` decorator.
"""
import sys

from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan import test_plan
from testplan.report.testing.styles import Style


@testsuite
class SimpleTest(object):

    # This will generate 4 new testcase methods, using a tuple for each one.
    @testcase(parameters=(
        (5, 5, 10),
        (3, 2, 5),
        (0, 0, 0),
        ('foo', 'bar', 'foobar')
    ))
    def addition(self, env, result, a, b, expected):
        result.equal(a + b, expected)
        # Parametrization context for the generated testcases will be:
        # result.equal(5 + 5, 10)
        # result.equal(3 + 2, 5)
        # result.equal(0 + 0, 0)()
        # result.equal('foo' + 'bar', 'foobar')

    # Combinatorial parametrization example
    # Associativity check of addition operation, (a + b = b + a)
    # This will generate 25 (5 x 5) methods.
    @testcase(parameters={
        'a': [1, 10, -5, -3.2, 3e12],
        'b': [0, 42, 4.2, -.231, 5.5e5]
    })
    def addition_associativity(self, env, result, a, b):
        # It's a good practice to generate a description
        # with the parametrized arguments as well.
        # So that you can have more context when you inspect the test report.
        result.equal(
            actual=a + b,
            expected=b + a,
            description='{a} + {b} == {b} + {a}'.format(a=a, b=b))

        # Generated testcases will have the following contexts:
        # result.equal(1 + 0, 0 + 1, ...)
        # result.equal(10 + 0, 0 + 10, ...)
        # result.equal(-5 + 0, 0 + -5, ...)
        # ...
        # ...
        # result.equal(3e12 + -.231, 3e12 + -.231, ...)
        # result.equal(3e12 + 5.5e5, 3e12 + 5.5e5, ...)

    # Shortcut notation that uses single values
    # for single argument parametrization
    # Assigns 1, 2, 3, 4 to `value` for each generated test case
    # Verbose notation would be
    # `parameters=((2,), (4,), (6,), (8,))` which is not that readable.
    @testcase(parameters=(
        2,  # first testcase
        4,  # second testcase
        6,  # third testcase
        8   # fourth testcase
    ))
    def is_even(self, env, result, value):
        result.equal(value % 2, 0)


# The example below makes use of a custom name
# generation function for parametrization.

# This way we can come up with more readable testcase
# method names on the test reports.

# If we didn't use a custom name function, we'd end up with method names
# like `func_raises_error__0`, `func_raises_error__1`
# But instead the custom function will give
# us names like `func_raises_error__ValueError`

def custom_error_name_func(func_name, kwargs):
    """Disregard `func` argument, use the error only."""
    return '{func_name}__{error_type}'.format(
        func_name=func_name,
        error_type=kwargs['error'].__name__
    )


@testsuite
class ErrorTest(object):

    # The lambda functions in the parameters below try to
    # execute invalid Python code that raises certain errors.
    # The parametrized test method checks if the function
    # raises the expected error when it is run.
    # This will generate 5 methods, for each item in the tuple.
    @testcase(
        parameters=(
            # tuple notation, using default error value (TypeError)
            ((lambda: 'foo' + 5),),
            # dict notation, using default error value (TypeError)
            {
                'func': lambda: 'foo' * 'foo',
            },
            (lambda: {'a': 5}['b'], KeyError),
            (lambda: int('a'), ValueError),
            (lambda: 10 / 0, ZeroDivisionError),
        ),
        # comment out the line below line to see how
        # Testplan falls back to simple method names with integer suffixes
        name_func=custom_error_name_func
    )
    def func_raises_error(self, env, result, func, error=TypeError):
        with result.raises(error):
            func()


# This function returns the value of the product directly
# which will be interpreted as a simple tag.
def simple_tag_func(kwargs):
    return kwargs['product'].title()


# This function returns a dictionary that is interpreted as a named tag.
def named_tag_func(kwargs):
    return {
        'product': kwargs['product'].title(),
    }


@testsuite
class ProductTest(object):
    """Sample testsuite that demonstrates how `tag_func` works."""

    @testcase(
        tags={'category': 'CategoryA'},
        parameters=(
            (2, 3, 'productA'),
            (3, 4, 'productB'),
        ),
        tag_func=simple_tag_func
    )
    def simple_tag_func_test(self, env, result, a, b, product):
        result.true(True)

    @testcase(
        tags={'category': 'CategoryB'},
        parameters=(
            (2, 3, 'productA'),
            (3, 4, 'productB'),
        ),
        tag_func=named_tag_func
    )
    def named_tag_func_test(self, env, result, a, b, product):
        result.true(True)


# Discard the original docstring, convert kwargs to str
def kwargs_to_string(docstring, kwargs):
    return str(kwargs)


# Use the original docstring, formatting
# it using kwargs via string interpolation.

# e.g. `foo: {foo}, bar: {bar}`.format(foo=2, bar=5)` -> 'foo: 2, bar: 5'
def interpolate_docstring(docstring, kwargs):
    return docstring.format(**kwargs)


@testsuite
class DocStringTest(object):

    @testcase(
        parameters=(
            (2, 3, 5),
            (5, 10, 15)
        ),
        docstring_func=kwargs_to_string
    )
    def addition_one(self, env, result, first, second, expected):
        """Test addition of two numbers."""
        return result.equal(first + second, expected)

    @testcase(
        parameters=(
            (2, 3, 5),
            (5, 10, 15)
        ),
        docstring_func=interpolate_docstring
    )
    def addition_two(self, env, result, first, second, expected):
        """
          Testing addition with: {first} + {second}
          Expected value: {expected}
        """
        return result.equal(first + second, expected)


@test_plan(
    name='Parametrization Example',
    # Using detailed assertions so we can
    # see testcase context for generated testcases
    stdout_style=Style('assertion-detail', 'assertion-detail')
)
def main(plan):
    plan.add(
        MultiTest(
            name='Primary',
            suites=[
                SimpleTest(),
                ErrorTest(),
                ProductTest(),
                DocStringTest()
            ]
        )
    )


if __name__ == '__main__':
    sys.exit(not main())
