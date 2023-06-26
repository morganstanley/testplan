"""Schema classes for test Reports."""

import functools
import json

from boltons.iterutils import remap, is_scalar

from marshmallow import Schema, fields, post_load
from marshmallow.utils import EXCLUDE

from testplan.common.serialization.schemas import load_tree_data
from testplan.common.serialization import fields as custom_fields
from testplan.common.report.schemas import (
    ReportSchema,
    ReportLogSchema,
    EventRecorderSchema,
)

from testplan.common.utils import timing

from .base import TestCaseReport, TestGroupReport, TestReport


__all__ = ["TestCaseReportSchema", "TestGroupReportSchema", "TestReportSchema"]

# pylint: disable=unused-argument


class IntervalSchema(Schema):
    """Schema for ``timer.Interval``"""

    start = custom_fields.UTCDateTime()
    end = custom_fields.UTCDateTime(allow_none=True)

    @post_load
    def make_interval(self, data, **kwargs):
        """Create an Interal object."""
        return timing.Interval(**data)


class TagField(fields.Field):
    """Field for serializing tag data, which is a ``dict`` of ``set``."""

    def _serialize(self, value, attr, obj, **kwargs):
        return {
            tag_name: list(tag_values)
            for tag_name, tag_values in value.items()
        }

    def _deserialize(self, value, attr, data, **kwargs):
        return {
            tag_name: set(tag_values) for tag_name, tag_values in value.items()
        }


class TimerField(fields.Field):
    """
    Field for serializing ``timer.Timer`` objects, which is a ``dict``
    of ``timer.Interval``.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        return {k: IntervalSchema().dump(v) for k, v in value.items()}

    def _deserialize(self, value, attr, data, **kwargs):
        return timing.Timer(
            {k: IntervalSchema().load(v) for k, v in value.items()}
        )


class EntriesField(fields.Field):
    """
    Handle encoding problems gracefully
    """

    @staticmethod
    def _json_serializable(v):
        try:
            json.dumps(v, ensure_ascii=True)
        except (UnicodeDecodeError, TypeError):
            return False
        else:
            return True

    def _serialize(self, value, attr, obj, **kwargs):
        # we don't need a _deserialize() here as we don't (and can't)
        # convert str back to non-json-serializable.
        def visit(parent, key, _value):
            """
            return
                True - keep the node unchange
                False - remove the node
                tuple - update the node data.
            """
            if is_scalar(_value) and not self._json_serializable(_value):
                return key, str(_value)
            return True

        return remap(value, visit=visit)


class TestCaseReportSchema(ReportSchema):
    """Schema for ``testing.TestCaseReport``"""

    source_class = TestCaseReport

    status_override = fields.String(allow_none=True)
    status_reason = fields.String(allow_none=True)

    entries = fields.List(EntriesField())

    category = fields.String(dump_only=True)
    status = fields.String()
    runtime_status = fields.String()
    counter = fields.Dict(dump_only=True)
    suite_related = fields.Bool()
    timer = TimerField(required=True)
    tags = TagField()

    @post_load
    def make_report(self, data, **kwargs):
        """
        Create the report object, assign ``timer`` &
        ``status_override`` attributes explicitly
        """
        timer = data.pop("timer")
        status = data.pop("status")
        runtime_status = data.pop("runtime_status")

        # We can discard the type field since we know what kind of report we
        # are making.
        if "type" in data:
            data.pop("type")

        rep = super(TestCaseReportSchema, self).make_report(data)
        rep.timer = timer
        rep.status = status
        rep.runtime_status = runtime_status
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
    category = fields.String()

    entries = custom_fields.GenericNested(
        schema_context={
            TestCaseReport: TestCaseReportSchema,
            TestGroupReport: lambda: TestGroupReportSchema(),
        },
        many=True,
    )
    events = fields.Dict(
        keys=fields.String(), values=fields.Nested(EventRecorderSchema)
    )
    host = fields.String(allow_none=True)

    @post_load
    def make_report(self, data, **kwargs):
        """
        Propagate tag indices after deserialization
        """
        rep = super(TestGroupReportSchema, self).make_report(data)
        rep.propagate_tag_indices()
        return rep


class TestReportSchema(Schema):
    """Schema for test report root, ``testing.TestReport``."""

    class Meta:
        unknown = EXCLUDE

    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    uid = fields.String(required=True)
    category = fields.String(dump_only=True)
    timer = TimerField(required=True)
    meta = fields.Dict()
    label = fields.String(allow_none=True)

    status_override = fields.String(allow_none=True)
    status = fields.String()
    runtime_status = fields.String()
    tags_index = TagField(dump_only=True)
    information = fields.List(fields.List(fields.String()))
    counter = fields.Dict(dump_only=True)

    attachments = fields.Dict()
    logs = fields.Nested(ReportLogSchema, many=True)
    timeout = fields.Integer(allow_none=True)

    entries = custom_fields.GenericNested(
        schema_context={TestGroupReport: TestGroupReportSchema}, many=True
    )

    events = fields.Dict(
        keys=fields.String(), values=fields.Nested(EventRecorderSchema)
    )

    @post_load
    def make_test_report(self, data, **kwargs):
        """Create report object & deserialize sub trees."""
        load_tree = functools.partial(
            load_tree_data,
            node_schema=TestGroupReportSchema,
            leaf_schema=TestCaseReportSchema,
        )

        entry_data = data.pop("entries")
        status = data.pop("status")
        runtime_status = data.pop("runtime_status")
        timer = data.pop("timer")
        logs = data.pop("logs", [])

        test_plan_report = TestReport(**data)
        test_plan_report.entries = [load_tree(c_data) for c_data in entry_data]
        test_plan_report.propagate_tag_indices()

        test_plan_report.status = status
        test_plan_report.runtime_status = runtime_status
        test_plan_report.timer = timer
        test_plan_report.logs = logs

        return test_plan_report


class ShallowTestGroupReportSchema(Schema):
    """Schema for shallow serialization of ``TestGroupReport``."""

    class Meta:
        unknown = EXCLUDE

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

    entry_uids = fields.List(fields.String(), dump_only=True)
    parent_uids = fields.List(fields.String())
    logs = fields.Nested(ReportLogSchema, many=True)
    hash = fields.Integer(dump_only=True)
    env_status = fields.String(allow_none=True)
    strict_order = fields.Bool()

    @post_load
    def make_testgroup_report(self, data, **kwargs):
        timer = data.pop("timer")
        logs = data.pop("logs", [])

        group_report = TestGroupReport(**data)
        group_report.propagate_tag_indices()

        group_report.timer = timer
        group_report.logs = logs

        return group_report


class ShallowTestReportSchema(Schema):
    """Schema for shallow serialization of ``TestReport``."""

    class Meta:
        unknown = EXCLUDE

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
    entry_uids = fields.List(fields.String(), dump_only=True)
    parent_uids = fields.List(fields.String())
    logs = fields.Nested(ReportLogSchema, many=True)
    hash = fields.Integer(dump_only=True)

    @post_load
    def make_test_report(self, data, **kwargs):
        timer = data.pop("timer")
        logs = data.pop("logs", [])

        test_plan_report = TestReport(**data)
        test_plan_report.propagate_tag_indices()

        test_plan_report.timer = timer
        test_plan_report.logs = logs

        return test_plan_report
