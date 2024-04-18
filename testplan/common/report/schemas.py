"""
  Base schemas for report serialization.
"""
from marshmallow import Schema, fields, post_load
from marshmallow.utils import EXCLUDE

from testplan.common.serialization import fields as custom_fields
from testplan.common.serialization import schemas

from .base import EventRecorder, Report, ReportGroup

__all__ = ["ReportLogSchema", "ReportSchema", "ReportGroupSchema"]

# pylint: disable=unused-argument


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
    entries = fields.List(custom_fields.NativeOrPretty())
    parent_uids = fields.List(fields.String())

    uid = fields.String()
    logs = fields.Nested(ReportLogSchema, many=True)
    hash = fields.Integer(dump_only=True)

    @post_load
    def make_report(self, data, **kwargs):
        """Create report object, attach log list."""
        logs = data.pop("logs", [])
        rep = self.get_source_class()(**data)
        rep.logs = logs
        return rep


class ReportGroupSchema(ReportSchema):
    """Schema for ``base.ReportGroup``."""

    source_class = ReportGroup

    entries = custom_fields.GenericNested(
        schema_context={
            "Report": ReportSchema,
            "ReportGroup": lambda: ReportGroupSchema(),
        },
        many=True,
    )


class EventRecorderSchema(Schema):
    """Schema for ``base.EventRecorder``."""

    name = fields.String()
    event_type = fields.String()
    start_time = fields.Float(allow_none=True)
    end_time = fields.Float(allow_none=True)
    children = fields.Nested("EventRecorderSchema", many=True)

    @post_load
    def make_event_recorder(self, data, **kwargs):
        return EventRecorder.load(data)
