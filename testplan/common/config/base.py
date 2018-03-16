"""
Module containing configuration objects and utilities.
"""

import copy

from schema import Schema, Optional, And, Or, Use

from testplan.common.utils.interface import check_signature


ABSENT = Optional._MARKER


def validate_func(args_list):
    """Validate given function signature."""
    return lambda x: callable(x) and check_signature(x, args_list)


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


class Config(object):
    """
    Base class for creating a configuration object with a schema
    that can define default values and support inheritance.
    Configurations can have a parent-child relationship so that
    options not defined in the child, can be retrieved from parent.
    """

    def __init__(self, **options):
        self._parent = None
        self._cfg_input = options
        sch = self.configuration_schema()
        cschema = sch if isinstance(sch, Schema) else Schema(sch)
        self._options = cschema.validate(options)

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
    def schema(self):
        """Returns the raw schema."""
        return self._schema

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

    def copy(self, **options):
        """
        Create a new configuration object and replace its options with
        the given option values.
        """
        # TODO dicuss problem validating DefaultValueWrapper values
        new_options = {}
        for key in self._options:
            new_options[copy.deepcopy(key)] = copy.deepcopy(getattr(self, key))
        new_options.update(options)
        new = self.__class__(**new_options)
        # parent makes the object non-serializable
        # new.parent = self.parent
        return new

    # API support
    replace = copy

    def configuration_schema(self):
        """
        To be implemented by the subclasses and return the config schema.
        """
        raise NotImplementedError

    @staticmethod
    def inherit_schema(target, source):
        """
        Returns a schema after overriding source options with target options.

        :param target: Configuration options overrides.
        :type target: ``Schema`` or ``dict``
        :param source: Source object with configuration schema.
        :type source: subclass of
                      :py:class:`Config <testplan.common.config.base.Config>`
        :return: Schema for the configuration validation.
        :rtype: ``Schema``
        """
        if isinstance(target, Schema):
            target_schema_dict = getattr(target, '_schema').copy()
        else:
            # dictionary expected
            target_schema_dict = target

        parent_schema = source.configuration_schema()
        if isinstance(parent_schema, Schema):
            parent_schema_dict = getattr(parent_schema, '_schema').copy()
        else:
            parent_schema_dict = parent_schema

        for parent_key in parent_schema_dict:
            real_parent_key = getattr(parent_key, '_schema', parent_key)
            found = False
            for target_key in list(target_schema_dict.keys()):
                real_target_key = getattr(target_key, '_schema', target_key)
                if real_parent_key == real_target_key:
                    found = True
                    break
            if not found:
                target_schema_dict[parent_key] = parent_schema_dict[parent_key]

        ignore_extra_keys = getattr(target, '_ignore_extra_keys', False)
        return Schema(target_schema_dict,
                      ignore_extra_keys=ignore_extra_keys)
