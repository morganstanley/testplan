"""
Custom marshmallow fields.
"""
import abc
import pprint

import pytz
from dateutil import parser
from lxml import etree

from marshmallow import fields
from marshmallow import class_registry
from marshmallow.base import SchemaABC
from marshmallow.utils import missing as missing_

from testplan.common.utils import comparison

# We explicitly enumerate types that are known to be safe to serialize by
# pickle. All other types will be converted to strings before pickling.
# types.NoneType is gone in python3 so we inspect the type of None directly.
COMPATIBLE_TYPES = (bool, float, type(None), str, bytes, int)

# pylint: disable=unused-argument


class Serializable(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def serialize(self):
        pass


class LogLink(Serializable):
    """
    Save an HTML link in WebUI
    """

    def __init__(self, link, title=None, new_window=True, inner=False):
        """
        :param link: The URL of the page the link goes to.
        :type link: ``str``
        :param title: The name of the link.
        :type title: ``str``
        :param new_window: Open the link on new window or not. Default is True.
        :type new_window: ``bool``
        :param inner: Link to internal page (report uid as the prefix). Default is False.
        :type new_window: ``bool``
        """
        self.link = link
        self.title = title or link
        self.new_window = new_window
        self.inner = inner

    def serialize(self):
        return {
            "link": self.link,
            "title": self.title,
            "new_window": self.new_window,
            "inner": self.inner,
            "type": "link",
        }


class FormattedValue(Serializable):
    """
    Save a formatted value in WebUI
    """

    def __init__(self, value, display):
        """
        :param value: The value of the data for sorting in the report.
        :type value: ``Union[str, numbers.Real]``
        :param display: Formatted value for display in the report.
        :type display: ``str``
        """
        self.value = value
        self.display = display

    def serialize(self):
        return {
            "value": self.value,
            "display": self.display,
            "type": "formattedValue",
        }


def _repr_obj(obj):
    # copypasta from unittest code
    try:
        return repr(obj)
    except Exception:
        return object.__repr__(obj)


def native_or_pformat(value):
    """Generic serialization compatible value formatter."""
    if comparison.is_regex(value):
        value = "REGEX({})".format(value.pattern)
    elif isinstance(value, comparison.Callable):
        value = str(value)
    elif callable(value):
        value = getattr(value, "__name__", _repr_obj(value))

    # For basic builtin types we return the value unchanged. All other types
    # will be formatted as strings.
    if type(value) in COMPATIBLE_TYPES:
        result = value
    else:
        result = pprint.pformat(value)

    return result


def native_or_pformat_dict(value):
    """
    Converter utility for dictionaries,
    converts values to JSON friendly format
    """
    return {k: native_or_pformat(v) for k, v in value.items()}


def native_or_pformat_list(value):
    """Converter utility for lists, converts values to JSON friendly format"""
    return [native_or_pformat(v) for v in value]


class Unicode(fields.Field):
    """
    Field that tries to convert value into a unicode

    object with the given codecs. Marshmallow internally decodes to
    utf-8 encoding, however it fails on Python 2 for str values
    like ``@t\xe9\xa7t\xfel\xe5\xf1``.

    So we have this field with explicit codecs instead.
    """

    codecs = ["utf-8", "latin-1"]  # Ideally we will let users override this

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, str) or value is None:
            return value

        elif isinstance(value, bytes):
            for codec in self.codecs:
                try:
                    return str(value, codec)
                except UnicodeDecodeError:
                    pass
            raise ValueError(
                "Could not decode {value} to unicode"
                " with the given codecs: {codecs}".format(
                    value=value, codecs=self.codecs
                )
            )
        else:
            return str(value)


class NativeOrPretty(fields.Field):
    """
    Uses serialization compatible native values
    or pretty formatted str representation.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, Serializable):
            return value.serialize()
        else:
            return native_or_pformat(value)


class NativeOrPrettyDict(fields.Field):
    """
    Dictionary serialization with native or pretty formatted values.
    Keys should be JSON serializable (str type),
    should be used for flat dicts only.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, dict):
            raise TypeError(
                "`value` ({value}) should be"
                " `dict` type, it was: {type}".format(
                    value=value, type=type(value)
                )
            )

        for k in value:
            if not isinstance(k, str):
                raise TypeError(
                    "`key` ({key}) should be of"
                    " `str` type, it was: {type}".format(key=k, type=type(k))
                )

        return native_or_pformat_dict(value)


# TODO: Move to entries
class RowComparisonField(fields.Field):
    """Serialization logic for RowComparison"""

    def _serialize(self, value, attr, obj, **kwargs):
        idx, row, diff, errors, extra = value
        return (
            idx,
            native_or_pformat_list(row),
            native_or_pformat_dict(diff),
            native_or_pformat_dict(errors),
            native_or_pformat_dict(extra),
        )


class SliceComparisonField(fields.Field):
    """Serialization logic for SliceComparison"""

    def _serialize(self, value, attr, obj, **kwargs):
        def str_or_iterable(val):
            return val if isinstance(val, str) else native_or_pformat_list(val)

        slice_obj, comp_indices, mismatch_indices, actual, expected = value

        return (
            repr(slice_obj),
            comp_indices,
            mismatch_indices,
            str_or_iterable(actual),
            str_or_iterable(expected),
        )


class ColumnContainComparisonField(fields.Field):
    """Serialization logic for ColumnContainComparison"""

    def _serialize(self, value, attr, obj, **kwargs):

        return (value.idx, native_or_pformat(value.value), value.passed)


class XMLElementField(fields.Field):
    """Custom field for `lxml.etree.Element serialization`."""

    def _serialize(self, value, attr, obj, **kwargs):
        return etree.tostring(value, pretty_print=True).decode("utf-8")


class ClassName(fields.Field):
    """Return the class name of the `obj`."""

    _CHECK_ATTRIBUTE = False

    class Meta:  # pylint: disable=bad-option-value,old-style-class,missing-docstring,no-init
        dump_only = True

    def _serialize(self, value, attr, obj, **kwargs):
        return obj.__class__.__name__


class DictMatch(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        keys = ("value", "ignore", "only")
        return {key: getattr(value, key) for key in keys}


class GenericNested(fields.Field):
    """
    Marshmallow does not support multiple schemas
    for a single `Nested` field.

    There is a project (marshmallow-oneofschema)
    that has similar functionality but it doesn't support
    self-referencing schemas, which is
    needed for serializing tree structures.

    This field should be used along with `ClassNameField`
    to return the type (class name) of the objects,
    so it can choose the correct schema during deserialization.
    """

    def __init__(
        self, schema_context, type_field="type", default=missing_, **kwargs
    ):
        self.schema_context = schema_context
        self.type_field = type_field
        self.many = kwargs.get("many", False)
        super(GenericNested, self).__init__(default=default, **kwargs)

    def _get_schema_obj(self, schema_value):
        parent_ctx = getattr(self.parent, "context", {})

        if callable(schema_value) and not isinstance(schema_value, type):
            schema_value = schema_value()

        if isinstance(schema_value, SchemaABC):
            schema_value.context.update(parent_ctx)
            return schema_value

        elif isinstance(schema_value, type) and issubclass(
            schema_value, SchemaABC
        ):
            return schema_value(many=self.many, context=parent_ctx)

        elif isinstance(schema_value, str):
            if schema_value == "self":
                return self.parent.__class__(
                    many=self.many, context=parent_ctx
                )
            else:
                schema_class = class_registry.get_class(schema_value)
                return schema_class(many=self.many, context=parent_ctx)

        raise ValueError(
            "Invalid value for schema: {}, {}".format(
                schema_value, type(schema_value)
            )
        )

    @property
    def schemas(self):
        """Return schema mapping in `<CLASS_NAME>: <SCHEMA_OBJECT>` format."""
        result = {}
        for object_type, schema_value in self.schema_context.items():
            if isinstance(object_type, str):
                key = object_type
            elif isinstance(object_type, type):
                key = object_type.__name__
            else:
                raise ValueError(
                    "Invalid value for object type ({}), strings"
                    " and class objects are allowed.".format(object_type)
                )

            result[key] = self._get_schema_obj(schema_value)
        return result

    def _serialize(self, nested_obj, attr, obj, **kwargs):

        if nested_obj is None:
            return None

        schemas = self.schemas

        if isinstance(nested_obj, (list, tuple)):
            return [self._serialize(nobj, attr, obj) for nobj in nested_obj]

        class_name = nested_obj.__class__.__name__

        if class_name not in schemas:
            raise KeyError(
                "No schema declaration found in"
                " `schema_context` for : {}".format(class_name)
            )

        schema_obj = schemas[class_name]
        return schema_obj.dump(nested_obj, many=False)


class UTCDateTime(fields.DateTime):
    """
    A formatted datetime string that represents UTC time. Naive datetime
    will be thought as in UTC timezone.
    Example: 2014-12-22T03:12:58.019077+00:00  (always ends with '+00:00')
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None

        return (
            value.replace(tzinfo=pytz.UTC)
            if value.tzinfo is None
            else value.astimezone(tz=pytz.UTC)
        ).isoformat()

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None

        dt = parser.parse(value)
        return (
            dt.replace(tzinfo=pytz.UTC)
            if dt.tzinfo is None
            else dt.astimezone(tz=pytz.UTC)
        )


class LocalDateTime(fields.DateTime):
    """
    A formatted datetime string that represents machine time. Naive datetime
    will be thought as in local timezone.
    Example: 2014-12-22T11:12:58.019077+08:00

    Note: Since Python 3.6 `datetime.datetime.astimezone` method can be called
    on naive instances that are presumed to represent system local time.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        return None if value is None else value.astimezone().isoformat()

    def _deserialize(self, value, attr, data, **kwargs):
        return None if value is None else parser.parse(value).astimezone()


class ExceptionField(fields.Field):
    """
    Serialize exceptions type and message.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        return (str(type(value)), str(value))
