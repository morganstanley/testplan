"""
Module containing configuration objects and utilities.
"""

import copy
import inspect

from schema import Schema, Optional, And, Or, Use

from testplan.common.utils.interface import check_signature
from testplan.common.utils import logger

# A sentinel object meaning not defined, it is useful when you need to
# handle arbitrary objects (including None).
ABSENT = Optional._MARKER


def validate_func(*arg_names):
    """Validate given function signature."""
    return lambda x: callable(x) and check_signature(x, list(arg_names))


def ConfigOption(key, default=ABSENT):
    """
    Wrapper around Optional, subclassing is not an option
    as Schema library does internal type checks as `type(obj) is Optional`.

    User can specify a default value when defining a config option. If not
    specified, it takes ABSENT as default value.

    When accessing a config option of an entity, we will first look in the
    config object of the entity itself (this also includes the options that
    are inherited from its parent). If a particular option is not defined or
    defined but only has an ABSENT value, we will recursively look in the
    entity's container until we find it. Typical containing relationships
    are like TestRunner contains Pool, TestRunner contains Multitest,
    Pool contains worker etc.

    Thus a config option takes one of these values in descending precedence:
        user specified -> a non-ABSENT default -> container's value

    Exception will be throw if we cannot find a valid value for a config
    option after we exhaust the entity's containers.
    """

    optional = Optional(key, default=default)
    optional.is_optional = True
    return optional


class Configurable(logger.Loggable):
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

        # this option is defined in current entity
        if name in options:
            # has user specified or valid default value
            if options[name] is not ABSENT:
                return options[name]

        # else: try to get this option from the entity's container
        if self.parent:
            return getattr(self.parent, name)
        else:
            raise AttributeError('Name: {}'.format(name))

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
        new_options = {}
        for key in self._options:
            value = getattr(self, key)
            if inspect.isclass(value) or inspect.isroutine(value):
                # Skipping non-serializable classes and routines.
                logger.TESTPLAN_LOGGER.warning(
                    'Skip denormalizing option: {}'.format(key))
                continue
            try:
                new_options[copy.deepcopy(key)] = copy.deepcopy(value)
            except Exception as exc:
                logger.TESTPLAN_LOGGER.warning(
                    'Failed to denormalize option: {} - {}'.format(key, exc))

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
