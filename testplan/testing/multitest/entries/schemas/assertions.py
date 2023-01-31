"""
Schema definitions for serializing Assertion objects. This will be a one-way
conversion, meaning that the reports and exports will be using the serialized
data directly.

The reason being some assertion classes may have attributes that
cannot be deserialized (processes, exception objects etc).
"""
from marshmallow import fields
from testplan.common.serialization import fields as custom_fields

from .base import BaseSchema, registry
from .. import assertions as asr

# pylint: disable=missing-docstring, abstract-method


@registry.bind_default(category="assertion")
class AssertionSchema(BaseSchema):
    passed = fields.Boolean()


@registry.bind(asr.RawAssertion)
class RawAssertionSchema(AssertionSchema):
    content = fields.String()


@registry.bind(
    asr.NotEqual,
    asr.Less,
    asr.LessEqual,
    asr.Greater,
    asr.GreaterEqual,
)
class FuncAssertionSchema(AssertionSchema):

    first = custom_fields.NativeOrPretty()
    second = custom_fields.NativeOrPretty()
    label = fields.String()


@registry.bind(asr.Equal)
class EqualSchema(FuncAssertionSchema):

    type_actual = fields.String()
    type_expected = fields.String()


@registry.bind(asr.Fail)
class FailSchema(AssertionSchema):
    message = fields.Raw()


@registry.bind(asr.IsClose)
class ApproximateEqualitySchema(AssertionSchema):

    first = custom_fields.NativeOrPretty()
    second = custom_fields.NativeOrPretty()
    rel_tol = custom_fields.NativeOrPretty()
    abs_tol = custom_fields.NativeOrPretty()
    label = fields.String()


@registry.bind(asr.IsTrue, asr.IsFalse)
class BooleanSchema(AssertionSchema):

    expr = custom_fields.NativeOrPretty()


@registry.bind(asr.Contain, asr.NotContain)
class MembershipSchema(AssertionSchema):

    member = custom_fields.NativeOrPretty()
    container = custom_fields.NativeOrPretty()


@registry.bind(
    asr.RegexMatch,
    asr.RegexMatchNotExists,
    asr.RegexSearch,
    asr.RegexSearchNotExists,
)
class RegexSchema(AssertionSchema):

    string = custom_fields.NativeOrPretty()
    pattern = custom_fields.NativeOrPretty()
    flags = fields.Integer()
    match_indexes = fields.List(fields.List(fields.Integer()))


@registry.bind(asr.RegexMatchLine)
class RegexMatchLineSchema(RegexSchema):

    match_context = fields.List(fields.Dict())


@registry.bind(asr.RegexFindIter)
class RegexFindIterSchema(RegexSchema):

    condition_match = fields.Boolean()
    condition = custom_fields.NativeOrPretty()


@registry.bind(asr.ExceptionRaised, asr.ExceptionNotRaised)
class ExceptionRaisedSchema(AssertionSchema):

    raised_exception = custom_fields.ExceptionField()
    expected_exceptions = fields.List(custom_fields.NativeOrPretty())

    pattern = custom_fields.Unicode(allow_none=True)
    func = fields.String(allow_none=True)

    exception_match = fields.Boolean()
    func_match = fields.Boolean()
    pattern_match = fields.Boolean()


@registry.bind(asr.EqualSlices, asr.EqualExcludeSlices)
class EqualSlicesSchema(AssertionSchema):

    data = fields.List(custom_fields.SliceComparisonField())
    included_indices = fields.List(fields.Integer())
    actual = fields.List(custom_fields.NativeOrPretty())
    expected = fields.List(custom_fields.NativeOrPretty())


@registry.bind(asr.LineDiff)
class LineDiffSchema(AssertionSchema):

    first = fields.List(custom_fields.NativeOrPretty())
    second = fields.List(custom_fields.NativeOrPretty())
    ignore_space_change = custom_fields.NativeOrPretty()
    ignore_whitespaces = custom_fields.NativeOrPretty()
    ignore_blank_lines = custom_fields.NativeOrPretty()
    unified = custom_fields.NativeOrPretty()
    context = custom_fields.NativeOrPretty()
    delta = fields.List(custom_fields.NativeOrPretty())


class ProcessExitStatusSchema(AssertionSchema):

    process = custom_fields.NativeOrPretty()
    expected_retcode = fields.Integer()
    core_file = fields.String()


@registry.bind(asr.ColumnContain)
class ColumnContainSchema(AssertionSchema):

    # table = fields.List(custom_fields.NativeOrPrettyDict())
    values = fields.List(custom_fields.NativeOrPretty())
    column = fields.String()
    limit = fields.Integer()
    report_fails_only = fields.Boolean()
    data = fields.List(custom_fields.ColumnContainComparisonField())


@registry.bind(asr.TableMatch, asr.TableDiff)
class TableMatchSchema(AssertionSchema):

    strict = fields.Boolean()

    columns = fields.List(fields.String(), attribute="display_columns")

    # Row data with diffs, errors, extra ctx for comparators
    data = fields.List(custom_fields.RowComparisonField())

    include_columns = fields.List(fields.String(), allow_none=True)
    exclude_columns = fields.List(fields.String(), allow_none=True)
    message = fields.String(allow_none=True)
    fail_limit = fields.Integer()
    report_fails_only = fields.Bool()


@registry.bind(asr.XMLCheck)
class XMLCheckSchema(AssertionSchema):

    xpath = fields.String()
    tags = fields.List(fields.String())

    xml = custom_fields.XMLElementField(attribute="element")

    namespaces = fields.Dict()
    data = fields.List(fields.List(custom_fields.NativeOrPretty()))
    message = fields.String()


@registry.bind(asr.DictCheck, asr.FixCheck)
class DictCheckSchema(AssertionSchema):

    has_keys = fields.List(custom_fields.NativeOrPretty())
    has_keys_diff = fields.List(custom_fields.NativeOrPretty())

    absent_keys = fields.List(custom_fields.NativeOrPretty())
    absent_keys_diff = fields.List(custom_fields.NativeOrPretty())


@registry.bind(asr.DictMatch, asr.FixMatch)
class DictMatchSchema(AssertionSchema):

    include_keys = fields.List(custom_fields.NativeOrPretty())
    exclude_keys = fields.List(custom_fields.NativeOrPretty())
    actual_description = fields.String()
    expected_description = fields.String()
    comparison = fields.Raw()


@registry.bind(asr.DictMatchAll, asr.FixMatchAll)
class DictMatchAllSchema(AssertionSchema):

    key_weightings = fields.Raw()
    matches = fields.Function(lambda obj: {"matches": obj.matches})
