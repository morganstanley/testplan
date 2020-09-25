"""
This module contains helper validation functions
to be used with configuration schemas.
"""
import warnings

import six
import validators


def is_subclass(parent_kls):
    """
    Validator for subclass check.

    When we have a class as a value in a validation schema, schema.py will
    implicitly try to do an ``isinstance`` check on the
    ``dict`` to be validated.

    Using this function will allow us to do ``issubclass`` checks.
    """

    def _validator(kls):
        return issubclass(kls, parent_kls)

    return _validator


def has_method(method_name):
    """Validator that checks if a given class has method with the given name"""

    def _validator(kls):
        return hasattr(kls, method_name) and callable(
            getattr(kls, method_name)
        )

    return _validator


def is_valid_url(url):
    """Validator that checks if a url is valid"""
    return bool(validators.url(url))


def is_valid_email(email):
    """Validator that checks if an email is valid"""
    return bool(validators.email(email))


def validate_display_name(name, length, description):
    """Validator that checks if the name for UI display is valid."""
    if not isinstance(name, six.string_types):
        raise ValueError(
            '{desc} "{name}" must be a string, it is of type:'
            " {type}".format(name=name, desc=description, type=type(name))
        )

    if not name or len(name) > length:
        raise ValueError(
            '{desc} "{name}" must be a non-empty string with'
            " length not greater than {length}".format(
                name=name, desc=description, length=length
            )
        )

    if ":" in six.ensure_str(name):
        warnings.warn(
            "It is strongly suggested that {desc} contains no colon, but"
            " Testplan found [{name}]".format(name=name, desc=description)
        )
