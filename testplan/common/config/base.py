"""
Module containing configuration objects and utilities.
"""

import copy
import inspect

from schema import Schema, Optional, And, Or, Use

from testplan.common.utils.interface import check_signature


ABSENT = Optional._MARKER


def validate_func(*arg_names):
    """Validate given function signature."""
    return lambda x: callable(x) and check_signature(x, list(arg_names))


class DefaultValueWrapper(object):
    """
    Utility class for distinguishing if a value is passed as schema default.
    """

    def __init__(self, value, block_propagation=True):
        self.value = value
        self.block_propagation = block_propagation

    def __repr__(self):
        return '{}(value={}{})'.format(
            self.__class__.__name__, repr(self.value),
            '' if self.block_propagation else ', propagation==True'
        )


def ConfigOption(key, default=ABSENT, block_propagation=True):
    """
    Wrapper around Optional, subclassing is not an option
    as Schema library does internal type checks as `type(obj) is Optional`.

    A config option usually has a default value, if user explicitly sets a
    value in config option, we call it local value. A config is composed of
    many options, it can also have a parent. For example, a TestplanConfig
    object belongs to a Testplan object, and a MultiTestConfig object belongs
    to a MultiTest object, while the Testplan object could be the owner of
    other MultiTest objects, thus, the TestplanConfig object can be set as
    the parent of these MultiTestConfig object. When we want to look up an
    option in those config objects, we have 2 ways:
        local -> default -> parent local -> parent default
        local -> parent local -> parent default -> default

    By default we apply the former strategy, but sometimes we need the latter.
    Think that you have a 'display_style' option in config, then you can
    customize the output. If multitests were added to testplan, where there is
    also such a 'display_style' option in its config, so we should apply the
    options from their parent.

    With `block_propagation` set to be False, the default value defined in
    parent class has higher priority to be retrieved.
    """

    optional = Optional(key, default=default)
    optional.is_optional = True
    if default is not ABSENT:
        optional.default = DefaultValueWrapper(default, block_propagation)
    return optional


class Configurable(object):
    """
    To be inherited by objects that accept configuration.
    """

    @classmethod
    def with_config(cls, **config):
        """
        Returns a tuple of class and configuration.
        """
        return cls, config


def update_options(target, source):
    """
    Given a target and source dictionary, update the target dict in place
    using the keys in source dict, if the keys do not exist in target.
    This is not simple dict update as in we can have target and source
    dicts like this:
    >>> target = {ConfigOption('foo'): int}
    >>> source = {'foo': int}
    For the example above, target will not be updated as the 'names' of the
    keys are the same, even if they don't have the same hash.
    """
    def get_key_str(option):
        """Will be used for getting name from ConfigOption keys."""
        return option._schema if isinstance(option, Optional) else option

    target_raw_keys = {get_key_str(k) for k in target}
    source_key_mapping = {get_key_str(k): k for k in source}

    for raw_key, key in source_key_mapping.items():
        if raw_key not in target_raw_keys:
            target[key] = source[key]


class Config(object):
    """
    Base class for creating a configuration object with a schema
    that can define default values and support inheritance.
    Configurations can have a parent-child relationship so that
    options not defined in the child, can be retrieved from parent.
    Supports composition of multiple config options via multiple inheritance.
    """

    ignore_extra_keys = False

    def __init__(self, **options):
        self._parent = None
        self._cfg_input = options
        self._options = self.build_schema().validate(options)

    def __getattr__(self, name):
        options = self.__getattribute__('_options')
        local_val = options[name] if name in options else ABSENT
        parent_val = ABSENT

        if local_val is not ABSENT and not isinstance(local_val,
                                                      DefaultValueWrapper):
            return local_val
        elif local_val is ABSENT or not getattr(local_val,
                                                'block_propagation', True):
            parent_val = getattr(self.parent, name,
                                 ABSENT) if self.parent else ABSENT

        if local_val is ABSENT and parent_val is ABSENT: 
            raise AttributeError('Name: {}'.format(name)) 

        if parent_val is not ABSENT:
            return parent_val
        elif isinstance(local_val, DefaultValueWrapper):
            return local_val.value

        raise RuntimeError('Error fetching attribute ({}) from {}'.format(
            name, self))

    def __repr__(self):
        return '{}{}'.format(self.__class__.__name__,
                             self._cfg_input or self._options)

    @property
    def parent(self):
        """Returns the parent configuration."""
        return self._parent

    @parent.setter
    def parent(self, value):
        """Set the parent configuration relation."""
        if self._parent is not None:
            raise AttributeError('Cannot overwrite parent: {}'.format(
                self._parent))
        self._parent = value

    def denormalize(self):
        """
        Create new config object that inherits all explicit attributes from
        its parents as well.
        """
        # TODO discuss problem validating DefaultValueWrapper values
        new_options = {}
        for key in self._options:
            value = getattr(self, key)
            if inspect.isclass(value) or inspect.isroutine(value):
                # Skipping non-serializable classes and routines.
                continue
            new_options[copy.deepcopy(key)] = copy.deepcopy(value)
        new = self.__class__(**new_options)
        return new

    @classmethod
    def get_options(cls):
        """Override this classmethod to provide extra config arguments."""
        raise NotImplementedError

    @classmethod
    def build_schema(cls):
        """
        Build a validation schema using the config options defined in
        this class and its parent classes.
        """
        config_options = cls.get_options().copy()

        # All parent classes that are subclasses of Config
        parents = [
            p for p in inspect.getmro(cls)[1:]
            if issubclass(p, Config) and p != Config
            ]

        for p in parents:
            update_options(target=config_options, source=p.get_options())

        return Schema(
            config_options,
            ignore_extra_keys=cls.ignore_extra_keys
        )
