"""
  Base schemas for report serialization.
"""
from marshmallow import Schema, fields, post_load
from marshmallow.utils import EXCLUDE

from testplan.common.serialization import fields as custom_fields
from testplan.common.serialization import schemas

# from .base import EventRecorder, Report, BaseReportGroup
from testplan.common.report import BaseReportGroup
from testplan.common.utils import timing
from .base import Report, BaseReportGroup

__all__ = ["ReportLogSchema", "ReportSchema", "ReportGroupSchema"]

# pylint: disable=unused-argument

class IntervalSchema(Schema):
    """Schema for ``timer.Interval``"""

    start = custom_fields.UTCDateTime()
    end = custom_fields.UTCDateTime(allow_none=True)

    @post_load
    def make_interval(self, data, **kwargs):
        """Create an Interal object."""
        return timing.Interval(**data)

class TimerField(fields.Field):
    """
    Field for serializing ``timer.Timer`` objects, which is a ``dict``
    of ``timer.Interval``.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        return {k: [IntervalSchema().dump(v) for v in l] for k, l in value.items()}

    def _deserialize(self, value, attr, data, **kwargs):
        return timing.Timer(
            {k: [IntervalSchema().load(v) for v in l] for k, l in value.items()}
        )



class ChildSchema(Schema):
    """
    Field for serializing ``timer.Timer`` objects, which is a ``dict``
    of ``timer.Interval``.
    """
    name = fields.String()
    timer = TimerField()
    children = fields.List(fields.Nested(lambda: ChildSchema()))


class ReportLogSchema(Schema):
    """Schema for log record data created by report stdout."""

    message = fields.String()
    levelname = fields.String()
    levelno = fields.Integer()
    created = custom_fields.UTCDateTime()
    funcName = fields.String()
    lineno = fields.Integer()
    uid = fields.UUID()


class ReportSchema(schemas.TreeNodeSchema):
    """Schema for ``base.Report``."""

    class Meta:
        unknown = EXCLUDE

    source_class = Report

    name = fields.String()
    description = fields.String(allow_none=True)
    definition_name = fields.String(
        allow_none=True
    )  # otherwise new tpr cannot process old report
    uid = fields.String()
    entries = fields.List(custom_fields.NativeOrPretty())
    parent_uids = fields.List(fields.String())

    hash = fields.Integer(dump_only=True)
    logs = fields.Nested(ReportLogSchema, many=True)
    status_override = fields.String(allow_none=True)
    status_reason = fields.String(allow_none=True)
    timer = TimerField(required=True)

    @post_load
    def make_report(self, data, **kwargs):
        """Create report object, attach log list."""
        logs = data.pop("logs", [])
        timer = data.pop("timer")

        rep = self.get_source_class()(**data)

        rep.logs = logs
        rep.timer = timer

        return rep


class BaseReportGroupSchema(ReportSchema):
    """Schema for ``base.BaseReportGroup``."""

    source_class = BaseReportGroup

    entries = custom_fields.GenericNested(
        schema_context={
            "Report": ReportSchema,
            "BaseReportGroup": lambda: BaseReportGroupSchema(),
        },
        many=True,
    )
    status = fields.String(dump_only=True)
    runtime_status = fields.String(dump_only=True)
    counter = fields.Dict(dump_only=True)

    children = fields.List(fields.Nested(ChildSchema))
#
# class EventRecorderSchema(Schema):
#     """Schema for ``base.EventRecorder``."""
#
#     name = fields.String()
#     event_type = fields.String()
#     start_time = fields.Float(allow_none=True)
#     end_time = fields.Float(allow_none=True)
#     children = fields.Nested("EventRecorderSchema", many=True)
#
#     @post_load
#     def make_event_recorder(self, data, **kwargs):
#         return EventRecorder.load(data)

