"""Schema classes for test Reports."""

import functools
import json

from boltons.iterutils import remap, is_scalar

from marshmallow import Schema, fields, post_load

from testplan.common.serialization.schemas import load_tree_data
from testplan.common.report.schemas import ReportSchema, ReportLogSchema
from testplan.common.serialization import fields as custom_fields

from testplan.common.utils import timing

from .base import TestCaseReport, TestGroupReport, TestReport

__all__ = ["TestCaseReportSchema", "TestGroupReportSchema", "TestReportSchema"]


class IntervalSchema(Schema):
    """Schema for ``timer.Interval``"""

    start = custom_fields.UTCDateTime()
    end = custom_fields.UTCDateTime(allow_none=True)

    @post_load
    def make_interval(self, data):  # pylint: disable=no-self-use
        """Create an Interal object."""
        return timing.Interval(**data)


class TagField(fields.Field):
    """Field for serializing tag data, which is a ``dict`` of ``set``."""

    def _serialize(self, value, attr, obj):
        return {
            tag_name: list(tag_values)
            for tag_name, tag_values in value.items()
        }

    def _deserialize(self, value, attr, data):
        return {
            tag_name: set(tag_values) for tag_name, tag_values in value.items()
        }


class TimerField(fields.Field):
    """
    Field for serializing ``timer.Timer`` objects, which is a ``dict``
    of ``timer.Interval``.
    """

    def _serialize(self, value, attr, obj):
        return {
            k: IntervalSchema(strict=True).dump(v).data
            for k, v in value.items()
        }

    def _deserialize(self, value, attr, data):
        return timing.Timer(
            {
                k: IntervalSchema(strict=True).load(v).data
                for k, v in value.items()
            }
        )


class EntriesField(fields.Field):
    """
    Handle encoding problems gracefully
    """

    _BYTES_KEY = "_BYTES_KEY"

    @staticmethod
    def _binary_to_hex_list(binary_obj):
        # make sure the hex repr is capitalized and leftpad'd with a zero
        # because '0x0C' is better than '0xc'.
        return [
            "0x{}".format(hex(b)[2:].upper().zfill(2))
            for b in bytearray(binary_obj)
        ]

    @staticmethod
    def _hex_list_to_binary(hex_list):
        return bytes(bytearray([int(x, 16) for x in hex_list]))

    def _serialize(self, value, attr, obj):
        def visit(parent, key, _value):
            def json_serializable(v):
                try:
                    json.dumps(_value, ensure_ascii=True)
                except (UnicodeDecodeError, TypeError):
                    return False
                else:
                    return True

            if is_scalar(_value) and not json_serializable(_value):
                return key, {self._BYTES_KEY: self._binary_to_hex_list(_value)}
            return True

        return remap(value, visit=visit)

    def _deserialize(self, value, attr, obj, recurse_lvl=0):
        def visit(parent, key, _value):
            if isinstance(_value, dict) and self._BYTES_KEY in _value:
                return key, self._hex_list_to_binary(_value[self._BYTES_KEY])
            return True

        return remap(value, visit=visit)


class TestCaseReportSchema(ReportSchema):
    """Schema for ``testing.TestCaseReport``"""

    source_class = TestCaseReport

    status_override = fields.String(allow_none=True)

    entries = fields.List(EntriesField())

    category = fields.String(dump_only=True)
    status = fields.String()
    runtime_status = fields.String(dump_only=True)
    counter = fields.Dict(dump_only=True)
    suite_related = fields.Bool()
    timer = TimerField(required=True)
    tags = TagField()

    status_reason = fields.String(allow_none=True)

    @post_load
    def make_report(self, data):
        """
        Create the report object, assign ``timer`` &
        ``status_override`` attributes explicitly
        """
        status_override = data.pop("status_override", None)
        timer = data.pop("timer")
        status = data.pop("status")

        # We can discard the type field since we know what kind of report we
        # are making.
        if "type" in data:
            data.pop("type")

        rep = super(TestCaseReportSchema, self).make_report(data)
        rep.status_override = status_override
        rep.timer = timer
        rep.status = status
        return rep


class TestGroupReportSchema(TestCaseReportSchema):
    """
    Schema for ``testing.TestGroupReportSchema``, supports tree serialization.
    """

    source_class = TestGroupReport
    part = fields.List(fields.Integer, allow_none=True)
    fix_spec_path = fields.String(allow_none=True)
    env_status = fields.String(allow_none=True)
    strict_order = fields.Bool()

    entries = custom_fields.GenericNested(
        schema_context={
            TestCaseReport: TestCaseReportSchema,
            TestGroupReport: "self",
        },
        many=True,
    )

    @post_load
    def make_report(self, data):
        """
        Propagate tag indices after deserialization
        """
        rep = super(TestGroupReportSchema, self).make_report(data)
        rep.propagate_tag_indices()
        return rep


class TestReportSchema(Schema):
    """Schema for test report root, ``testing.TestReport``."""

    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    uid = fields.String(required=True)
    category = fields.String(dump_only=True)
    timer = TimerField(required=True)
    meta = fields.Dict()

    status = fields.String()
    runtime_status = fields.String(dump_only=True)
    tags_index = TagField(dump_only=True)
    status_override = fields.String(allow_none=True)
    information = fields.List(fields.List(fields.String()))
    counter = fields.Dict(dump_only=True)

    attachments = fields.Dict()
    logs = fields.Nested(ReportLogSchema, many=True)
    timeout = fields.Integer(allow_none=True)

    entries = custom_fields.GenericNested(
        schema_context={TestGroupReport: TestGroupReportSchema}, many=True
    )

    @post_load
    def make_test_report(self, data):  # pylint: disable=no-self-use
        """Create report object & deserialize sub trees."""
        load_tree = functools.partial(
            load_tree_data,
            node_schema=TestGroupReportSchema,
            leaf_schema=TestCaseReportSchema,
        )

        entry_data = data.pop("entries")
        status = data.pop("status")
        status_override = data.pop("status_override")
        timer = data.pop("timer")
        timeout = data.pop("timeout", None)
        logs = data.pop("logs", [])

        test_plan_report = TestReport(**data)
        test_plan_report.entries = [load_tree(c_data) for c_data in entry_data]
        test_plan_report.propagate_tag_indices()

        test_plan_report.status = status
        test_plan_report.status_override = status_override
        test_plan_report.timer = timer
        test_plan_report.timeout = timeout
        test_plan_report.logs = logs
        return test_plan_report


class ShallowTestGroupReportSchema(Schema):
    """Schema for shallow serialization of ``TestGroupReport``."""

    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    uid = fields.String(required=True)
    category = fields.String()
    timer = TimerField(required=True)
    part = fields.List(fields.Integer, allow_none=True)
    fix_spec_path = fields.String(allow_none=True)
    status_override = fields.String(allow_none=True)
    status = fields.String(dump_only=True)
    runtime_status = fields.String(dump_only=True)
    counter = fields.Dict(dump_only=True)
    suite_related = fields.Bool()
    tags = TagField()
    entry_uids = fields.List(fields.Str(), dump_only=True)
    parent_uids = fields.List(fields.Str())
    hash = fields.Integer(dump_only=True)
    env_status = fields.String(allow_none=True)
    strict_order = fields.Bool()

    @post_load
    def make_testgroup_report(self, data):
        status_override = data.pop("status_override", None)
        timer = data.pop("timer")

        group_report = TestGroupReport(**data)
        group_report.status_override = status_override
        group_report.timer = timer
        group_report.propagate_tag_indices()

        return group_report


class ShallowTestReportSchema(Schema):
    """Schema for shallow serialization of ``TestReport``."""

    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    uid = fields.String(required=True)
    category = fields.String(dump_only=True)
    timer = TimerField(required=True)
    meta = fields.Dict()
    status = fields.String(dump_only=True)
    runtime_status = fields.String(dump_only=True)
    tags_index = TagField(dump_only=True)
    status_override = fields.String(allow_none=True)
    counter = fields.Dict(dump_only=True)
    attachments = fields.Dict()
    entry_uids = fields.List(fields.Str(), dump_only=True)
    parent_uids = fields.List(fields.Str())
    hash = fields.Integer(dump_only=True)

    @post_load
    def make_test_report(self, data):
        status_override = data.pop("status_override", None)
        timer = data.pop("timer")

        test_plan_report = TestReport(**data)
        test_plan_report.propagate_tag_indices()

        test_plan_report.status_override = status_override
        test_plan_report.timer = timer
        return test_plan_report
