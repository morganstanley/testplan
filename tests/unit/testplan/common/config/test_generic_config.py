"""TODO."""

import re
from schema import Schema, And, Or, Use, SchemaError

from testplan.common.entity import Entity
from testplan.common.config import Config, ConfigOption
from testplan.common.utils.exceptions import should_raise


class LambdaConfig(Config):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption('a', default=0.5): lambda x: 0 < x < 1,
            ConfigOption('b', default=2):
                lambda x: isinstance(x, (int, float))
        }


class First(Config):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption('a', default=1): int,
            ConfigOption('b', default=2): int,
            ConfigOption('c', default=3): int
        }


class Second(First):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption('a', default=6.0, block_propagation=False): float,
            ConfigOption('c', default=9.0, block_propagation=False): float,
            ConfigOption('d'): lambda x: isinstance(x, (int, float))
        }


class Third(Second):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption(
                'a', default=LambdaConfig(),
                block_propagation=False): Config,
            ConfigOption('c', default=-1): lambda x: x < 0
        }


def test_basic_config():
    """Basic config operations."""
    item = First()
    assert (1, 2, 3) == (item.a, item.b, item.c)

    item = First(a=5, b=4)
    assert (5, 4, 3) == (item.a, item.b, item.c)

    clone = item.denormalize()
    assert id(clone) != id(item)
    assert clone.parent is None
    assert (clone.a, clone.b, clone.c) == (item.a, item.b, item.c)


def test_basic_schema_fail():
    """Wrong type provided."""
    should_raise(SchemaError, First, kwargs=dict(a=1.0),
                 pattern=re.compile(r".*\n.*should be instance of 'int'.*",
                                    re.MULTILINE))
    should_raise(SchemaError, First, kwargs=dict(d=1.0),
                 pattern=re.compile(r".*Wrong keys? 'd'.*"))


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
    assert (6.0, 2, 9.0) == (item.a, item.b, item.c)
    assert item._options['a'].block_propagation == False
    assert item._options['c'].block_propagation == False

    item = Second(a=5.0, b=4)
    assert (5.0, 4, 9.0) == (item.a, item.b, item.c)
    assert item._options['c'].block_propagation == False

    item = Third()
    assert (0.5, 2, 2, -1) == (item.a.a, item.a.b, item.b, item.c)
    assert isinstance(item.a, LambdaConfig)
    assert item._options['a'].block_propagation == False
    assert item._options['c'].block_propagation == True

    item = Third(a=LambdaConfig(a=0.66, b=13), d=5)
    assert (0.66, 13, 2, 5) == (item.a.a, item.a.b, item.b, item.d)
    assert item._options['c'].block_propagation == True


class Root(Config):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption('foo', default=5): int,
            ConfigOption('bar', default=3): int
        }


class Branch(Config):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption('foo', default=50): int,
            ConfigOption('bar', default=30, block_propagation=False): int,
        }


class Leaf(Config):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption('foo', default=500, block_propagation=False): int,
            ConfigOption('bar', default=300, block_propagation=False): int,
            ConfigOption('baz', default='alpha'): str,
        }


def test_getattr_propagation():
    """
    Attribute retrieval should try explicitly set (local)
    values first (propagating from leaf to root), if nothing
    is found it should try default values (also propagating from
    leaf to root), but if attribute`block_propagation` of config option
    is set to False, retrieve the value from parent class at first.
    """
    root = Root()
    assert (root.foo, root.bar) == (5, 3)

    branch_1 = Branch()
    # foo -> branch default, bar -> branch default
    assert (branch_1.foo, branch_1.bar) == (50, 30)

    branch_1.parent = root
    # foo -> branch default, bar -> root default
    assert (branch_1.foo, branch_1.bar) == (50, 3)

    branch_2 = Branch(foo=15)
    # foo -> branch local, bar -> branch default
    assert (branch_2.foo, branch_2.bar) == (15, 30)

    branch_2.parent = root
    # foo -> branch local, bar -> root default
    assert (branch_2.foo, branch_2.bar) == (15, 3)

    branch_3 = Branch(bar=40)
    # foo -> branch default, bar -> branch local
    assert (branch_3.foo, branch_3.bar) == (50, 40)

    branch_3.parent = root
    # foo -> branch default, bar -> branch local
    assert (branch_3.foo, branch_3.bar) == (50, 40)

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

    leaf_2.parent = branch_2
    # foo -> leaf local, bar -> root default, baz -> leaf default
    assert (leaf_2.foo, leaf_2.bar, leaf_2.baz) == (111, 3, 'alpha')

    leaf_2 = Leaf(foo=111)
    leaf_2.parent = branch_3
    # foo -> leaf local, bar -> branch local, baz -> leaf default
    assert (leaf_2.foo, leaf_2.bar, leaf_2.baz) == (111, 40, 'alpha')

    leaf_3.parent = branch_2
    # foo -> branch local, bar -> leaf local, baz -> leaf default
    assert (leaf_3.foo, leaf_3.bar, leaf_3.baz) == (15, 222, 'alpha')

    leaf_3 = Leaf(bar=222)
    leaf_3.parent = branch_3
    # foo -> branch default, bar -> leaf local, baz -> leaf default
    assert (leaf_3.foo, leaf_3.bar, leaf_3.baz) == (50, 222, 'alpha')

    leaf_4 = Leaf(baz='beta')
    # foo -> leaf default, bar -> leaf default, baz -> leaf local
    assert (leaf_4.foo, leaf_4.bar, leaf_4.baz) == (500, 300, 'beta')

    leaf_4.parent = branch_2
    # foo -> branch local, bar -> root default, baz -> leaf local
    assert (leaf_4.foo, leaf_4.bar, leaf_4.baz) == (15, 3, 'beta')

    leaf_4 = Leaf(baz='beta')
    leaf_4.parent = branch_3
    # foo -> branch default, bar -> branch local, baz -> leaf local
    assert (leaf_4.foo, leaf_4.bar, leaf_4.baz) == (50, 40, 'beta')


class TopConfig(Config):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption('foo', default=None): (int, None),
            ConfigOption('boo', default=None): (list, None),
            ConfigOption('bar', default='hi', block_propagation=False): str,
            ConfigOption('baz', default='hey', block_propagation=False): str
        }


class Top(Entity):

    CONFIG = TopConfig
    def __init__(self, **options):
        super(Top, self).__init__(**options)


class MiddleConfig(TopConfig):

    @classmethod
    def get_options(cls):
        return {
            'name': str,
            ConfigOption('foo', default=9): int,
            ConfigOption('boo', default=[1, 2, 3]): list,
            ConfigOption('koo', default=99): int,
            ConfigOption('zoo', default={1: 'a', 2: 'b', 3: 'c'}): dict,
            ConfigOption('bar', default='hello', block_propagation=False): str,
            ConfigOption('baz', default='world', block_propagation=False): str
        }


class Middle(Top):

    CONFIG = MiddleConfig
    def __init__(self, **options):
        super(Middle, self).__init__(**options)


class BottomConfig(MiddleConfig):

    @classmethod
    def get_options(cls):
        return {
            ConfigOption('description', default=None): Or(str, None)
        }


class Bottom(Middle):

    CONFIG = BottomConfig
    def __init__(
        self, name, description=None, foo=9, boo=None, bar=None, **options
    ):
        options.update(self.filter_locals(locals()))
        self._options = options.copy()
        super(Bottom, self).__init__(**options)

    @property
    def options(self):
        return self._options


def test_filter_locals():
    """Test that Entity.filter_locals() works correctly."""
    bottom1 = Bottom('Bottom1')
    # Arguments defined explicitly in __init__() should appear and for mutable
    # type the origin values defined in config class will be retrieved.
    assert len(bottom1.options) == 4
    assert bottom1.options['name'] == 'Bottom1'
    assert bottom1.options['description'] == None
    assert bottom1.options['foo'] == 9
    assert bottom1.options['boo'] == [1, 2, 3]

    bottom2 = Bottom(
        'Bottom2', description='An example',
        boo=None, zoo={10: 'a', 20: 'b', 30: 'c'}, bar='barbar'
    )
    # Arguments defined explicitly in __init__() or passed to __init__()
    # should appear, explicitly passed values will overwrite the defaults.
    assert len(bottom2.options) == 6
    assert bottom2.options['name'] == 'Bottom2'
    assert bottom2.options['description'] == 'An example'
    assert bottom1.options['foo'] == 9
    assert bottom1.options['boo'] == [1, 2, 3]
    assert bottom2.options['zoo'] == {10: 'a', 20: 'b', 30: 'c'}
    assert bottom2.options['bar'] == 'barbar'
