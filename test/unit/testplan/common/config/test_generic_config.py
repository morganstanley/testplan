"""TODO."""

import re
from schema import Schema, And, Or, Use, SchemaError

from testplan.common.config import Config, ConfigOption
from testplan.common.utils.exceptions import should_raise


class LambdaConfig(Config):
    def configuration_schema(self):
        return Schema({ConfigOption('a', default=0.5):
                           lambda x: 0 < x < 1,
                       ConfigOption('b', default=2):
                           lambda x: isinstance(x, (int, float))})


class First(Config):
    def configuration_schema(self):
        return Schema({ConfigOption('a', default=1): int,
                       ConfigOption('b', default=2): int})


class Second(First):
    def configuration_schema(self):
        new = Schema({ConfigOption('a', default=6.0): float,
                      ConfigOption('c'):
                          lambda x: isinstance(x, (int, float))})
        return self.inherit_schema(new, super(Second, self))


class Third(Second):
    def configuration_schema(self):
        default = LambdaConfig()
        new = Schema({ConfigOption('a', default=default): Config})
        return self.inherit_schema(new, super(Third, self))


def test_basic_config():
    """Basic config operations."""
    item = First()
    assert (1, 2) == (item.a, item.b)

    item = First(a=2)
    assert (2, 2) == (item.a, item.b)

    # Copied configs
    three = item.copy(b=3)
    assert (2, 3) == (three.a, three.b)

    four = three.copy()
    assert id(four) != id(three)
    assert (four.a, four.b) == (three.a, three.b)


def test_basic_schema_fail():
    """Wrong type provided."""
    should_raise(SchemaError, First, kwargs=dict(a=1.0),
                 pattern=re.compile(r".*\n.*should be instance of 'int'.*",
                                    re.MULTILINE))
    should_raise(SchemaError, First, kwargs=dict(c=1.0),
                 pattern=re.compile(r".*Wrong keys 'c'.*"))


def test_lambda_matching():
    """Lambdas in schema."""

    item = LambdaConfig()
    assert (0.5, 2) == (item.a, item.b)

    item = LambdaConfig(a=0.99, b=2.0)
    assert (0.99, 2.0) == (item.a, item.b)


def test_lambda_failing():
    """Lambdas in schema."""
    for value in (0, 1):
        should_raise(SchemaError, LambdaConfig, kwargs=dict(a=value),
                     pattern=re.compile(r".*\n.*should evaluate to True",
                                        re.MULTILINE))
    for value in (object, '1'):
        should_raise(SchemaError, LambdaConfig, kwargs=dict(b=value),
                     pattern=re.compile(r".*\n.*should evaluate to True",
                                        re.MULTILINE))


def test_config_inheritance():
    """Inheritance of config and schemas."""
    item = Second()
    assert (6.0, 2) == (item.a, item.b)

    item = Second(a=5.0, b=4)
    assert (5.0, 4) == (item.a, item.b)

    item = Third()
    assert (0.5, 2, 2) == (item.a.a, item.a.b, item.b)
    assert isinstance(item.a, LambdaConfig)

    item = Third(a=LambdaConfig(a=0.66, b=13), c=5)
    assert (0.66, 13, 2, 5) == (item.a.a, item.a.b, item.b, item.c)


class Root(Config):
    def configuration_schema(self):
        return Schema({ConfigOption('foo', default=5): int})


class Branch(Config):
    def configuration_schema(self):
        return Schema({
            ConfigOption('foo', default=50): int,
            ConfigOption('bar', default=30): int,
        })


class Leaf(Config):
    def configuration_schema(self):
        return Schema({
            ConfigOption('foo', default=500): int,
            ConfigOption('bar', default=300): int,
            ConfigOption('baz', default='alpha'): str,
        })


def test_getattr_propagation():
    """
        Attribute retrieval should try explicitly set (local)
        values first (propagating from leaf to root), if nothing
        is found it should try default values
        (propagating from root to leaf)
    """
    root = Root()
    assert root.foo == 5

    branch_1 = Branch()
    assert (branch_1.foo, branch_1.bar) == (50, 30)
    branch_1.parent = root

    assert (branch_1.foo, branch_1.bar) == (5, 30)

    branch_2 = Branch(foo=15)
    # foo -> branch local, bar -> branch default
    assert (branch_2.foo, branch_2.bar) == (15, 30)

    branch_2.parent = root
    # foo -> branch local, bar -> branch default
    assert (branch_2.foo, branch_2.bar) == (15, 30)

    branch_3 = Branch(bar=40)

    # foo -> branch default, bar -> branch local
    assert (branch_3.foo, branch_3.bar) == (50, 40)
    branch_3.parent = root

    # foo -> root default, bar -> branch local
    assert (branch_3.foo, branch_3.bar) == (5, 40)

    branch_4 = Branch(foo=123, bar=333)
    # foo -> branch local, bar -> branch local
    assert (branch_4.foo, branch_4.bar) == (123, 333)
    branch_4.parent = root
    # foo -> branch local, bar -> branch local
    assert (branch_4.foo, branch_4.bar) == (123, 333)

    leaf_1 = Leaf()
    # foo -> leaf default, bar -> leaf default, baz -> leaf default
    assert (leaf_1.foo, leaf_1.bar, leaf_1.baz) == (500, 300, 'alpha')

    leaf_2 = Leaf(foo=111)
    # foo -> leaf local, bar -> leaf default, baz -> leaf default
    assert (leaf_2.foo, leaf_2.bar, leaf_2.baz) == (111, 300, 'alpha')

    leaf_3 = Leaf(bar=222)
    # foo -> leaf default, bar -> leaf local, baz -> leaf default
    assert (leaf_3.foo, leaf_3.bar, leaf_3.baz) == (500, 222, 'alpha')
    leaf_3.parent = branch_2
    # foo -> branch local, bar -> leaf local, baz -> leaf default
    assert (leaf_3.foo, leaf_3.bar, leaf_3.baz) == (15, 222, 'alpha')

    leaf_4 = Leaf(baz='beta')
    # foo -> leaf default, bar -> leaf default, baz -> leaf local
    assert (leaf_4.foo, leaf_4.bar, leaf_4.baz) == (500, 300, 'beta')
    leaf_4.parent = branch_3
    # foo -> root default, bar -> branch local, baz -> leaf local
    assert (leaf_4.foo, leaf_4.bar, leaf_4.baz) == (5, 40, 'beta')
