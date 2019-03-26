"""
  Custom marshmallow fields.
"""
import pprint
import six
import warnings
try:
    from lxml import etree
except Exception as exc:
    warnings.warn('lxml need to be supported: {}'.format(exc))
from dateutil import parser
import pytz

from marshmallow import fields
from marshmallow.compat import text_type, binary_type
from marshmallow.utils import missing as missing_
from marshmallow.base import SchemaABC
from marshmallow import class_registry
from marshmallow.fields import _RECURSIVE_NESTED
from marshmallow.exceptions import ValidationError

from testplan.common.utils import comparison

# from testip.alpha import util


# pylint: disable=unused-argument


# JSON & pickle Serialization compatible types
# types.NoneType is gone in python3
COMPATIBLE_TYPES = (
    bool, float, type(None)) + six.string_types + six.integer_types
MAX_LENGTH = 1000  # this will be configurable


def _repr_obj(obj):
    # copypasta from unittest code
    try:
        return repr(obj)
    except Exception:
        return object.__repr__(obj)


def native_or_pformat(value):
    """Generic serialization compatible value formatter."""
    if comparison.is_regex(value):
        value = 'REGEX({})'.format(value.pattern)
    elif isinstance(value, comparison.Callable):
        value = str(value)
    elif callable(value):
        value = getattr(value, '__name__', _repr_obj(value))

    result = value if isinstance(value, COMPATIBLE_TYPES) else pprint.pformat(value)
    obj_repr = _repr_obj(result)

    if len(obj_repr) > MAX_LENGTH:
        result = obj_repr[:MAX_LENGTH] + '[truncated]...'
    return result


def native_or_pformat_dict(value):
    """
        Converter utility for dictionaries,
        converts values to JSON friendly format
    """
    return {
        k: native_or_pformat(v) for k, v in value.items()
    }


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

    codecs = ['utf-8', 'latin-1']  # Ideally we will let users override this

    def _serialize(self, value, attr, obj):
        if isinstance(value, text_type) or value is None:
            return value

        elif isinstance(value, binary_type):
            for codec in self.codecs:
                try:
                    return text_type(value, codec)
                except UnicodeDecodeError:
                    pass
            raise ValueError(
                'Could not decode {value} to unicode'
                ' with the given codecs: {codecs}'.format(
                    value=value, codecs=self.codecs))
        else:
            return text_type(value)


class NativeOrPretty(fields.Field):
    """
        Uses serialization compatible native values
        or pretty formatted str representation.
    """

    def _serialize(self, value, attr, obj):
        return native_or_pformat(value)


class NativeOrPrettyDict(fields.Field):
    """
      Dictionary serialization with native or pretty formatted values.
      Keys should be JSON serializable (str type),
      should be used for flat dicts only.
    """
    def _serialize(self, value, attr, obj):
        if not isinstance(value, dict):
            raise TypeError(
                '`value` ({value}) should be'
                ' `dict` type, it was: {type}'.format(
                    value=value, type=type(value)))

        for k in value:
            if not isinstance(k, six.string_types):
                raise TypeError(
                    '`key` ({key}) should be of'
                    ' `str` type, it was: {type}'.format(key=k, type=type(k)))

        return native_or_pformat_dict(value)


# TODO: Move to entries
class RowComparisonField(fields.Field):
    """Serialization logic for RowComparison"""

    def _serialize(self, value, attr, obj):
        idx, row, diff, errors, extra = value
        return (
            idx,
            native_or_pformat_list(row),
            native_or_pformat_dict(diff),
            native_or_pformat_dict(errors),
            native_or_pformat_dict(extra)
        )


class SliceComparisonField(fields.Field):
    """Serialization logic for SliceComparison"""

    def _serialize(self, value, attr, obj):

        def str_or_iterable(val):
            return val if isinstance(val, six.string_types)\
                else native_or_pformat_list(val)

        slice_obj, comp_indices, mismatch_indices, actual, expected = value

        return (
            repr(slice_obj),
            comp_indices,
            mismatch_indices,
            str_or_iterable(actual),
            str_or_iterable(expected)
        )


class ColumnContainComparisonField(fields.Field):
    """Serialization logic for ColumnContainComparison"""

    def _serialize(self, value, attr, obj):

        return (
            value.idx,
            native_or_pformat(value.value),
            value.passed
        )



class XMLElementField(fields.Field):
    """Custom field for `lxml.etree.Element serialization`."""

    def _serialize(self, value, attr, obj):
        return etree.tostring(value, pretty_print=True)


class ClassName(fields.Field):
    """Return the class name of the `obj`."""

    _CHECK_ATTRIBUTE = False

    class Meta:  # pylint: disable=bad-option-value,old-style-class,missing-docstring,no-init
        dump_only = True

    def _serialize(self, value, attr, obj):
        return obj.__class__.__name__


class DictMatch(fields.Field):

    def _serialize(self, value, attr, obj):
        keys = ('value', 'ignore', 'only')
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
            self,
            schema_context,
            type_field='type',
            default=missing_, **kwargs
    ):
        self.schema_context = schema_context
        self.type_field = type_field
        self.many = kwargs.get('many', False)
        super(GenericNested, self).__init__(default=default, **kwargs)

    def _get_schema_obj(self, schema_value):
        parent_ctx = getattr(self.parent, 'context', {})

        if isinstance(schema_value, SchemaABC):
            schema_value.context.update(parent_ctx)
            return schema_value

        elif isinstance(schema_value, type) and\
                issubclass(schema_value, SchemaABC):
            return schema_value(many=self.many, context=parent_ctx)

        elif isinstance(schema_value, six.string_types):

            if schema_value == _RECURSIVE_NESTED:
                return self.parent.__class__(many=self.many, context=parent_ctx)
            else:
                schema_class = class_registry.get_class(schema_value)
                return schema_class(many=self.many, context=parent_ctx)

        raise ValueError(
            'Invalid value for schema: {}, {}'.format(
                schema_value, type(schema_value)))

    @property
    def schemas(self):
        """Return schema mapping in `<CLASS_NAME>: <SCHEMA_OBJECT>` format."""
        result = {}
        for object_type, schema_value in self.schema_context.items():
            if isinstance(object_type, six.string_types):
                key = object_type
            elif isinstance(object_type, type):
                key = object_type.__name__
            else:
                raise ValueError(
                    'Invalid value for object type ({}), strings'
                    ' and class objects are allowed.'.format(object_type))

            result[key] = self._get_schema_obj(schema_value)
        return result

    def _serialize(self, nested_obj, attr, obj):

        if nested_obj is None:
            return None

        schemas = self.schemas

        if isinstance(nested_obj, (list, tuple)):
            return [self._serialize(nobj, attr, obj) for nobj in nested_obj]

        class_name = nested_obj.__class__.__name__

        if class_name not in schemas:
            raise KeyError(
                'No schema declaration found in'
                ' `schema_context` for : {}'.format(class_name))

        schema_obj = schemas[class_name]

        ret, errors = schema_obj.dump(
            nested_obj, many=False, update_fields=False)

        if errors:
            raise ValidationError(errors, data=ret)
        return ret


class UTCDateTime(fields.DateTime):
    """
      While parsing timestamps, original `fields.Datetime` tries
      to use ``dateutil`` if it's available.

      Unfortunately, the way it does the check for ``dateutil``
      availability is not compatible with our internal environment

      If the ``dateutil`` is not available, it falls back to
      ``datetime.datetime.strptime`` which leaves the
      millisecond information out.

      So we specify the deserialization logic explicitly to
      make use of dateutil. In addition we use ``pytz``
      timezones instead of ``dateutil.tz``.
    """

    def _deserialize(self, value, attr, data):
        return parser.parse(value).replace(tzinfo=pytz.UTC)

class ExceptionField(fields.Field):
    """
    Serialize exceptions type and message.
    """

    def _serialize(self, value, attr, obj):
        return (str(type(value)), str(value))
