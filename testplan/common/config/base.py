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

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '{}(value={})'.format(self.__class__.__name__, repr(self.value))


def ConfigOption(key, default=ABSENT):
    """
    Wrapper around Optional, subclassing is not an option
    as Schema library does internal type checks as `type(obj) is Optional`.
    """

    optional = Optional(key, default=default)
    optional.is_optional = True
    if default is not ABSENT:
        optional.default = DefaultValueWrapper(default)
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
        parent_val = getattr(self.parent, name,
                             ABSENT) if self.parent else ABSENT

        if local_val is ABSENT and parent_val is ABSENT:
            raise AttributeError('Name: {}'.format(name))

        if local_val is not ABSENT and not isinstance(local_val,
                                                      DefaultValueWrapper):
            return local_val
        elif parent_val is not ABSENT:
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
        # TODO dicuss problem validating DefaultValueWrapper values
        new_options = {}
        for key in self._options:
            new_options[copy.deepcopy(key)] = copy.deepcopy(getattr(self, key))
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
