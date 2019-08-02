"""
  Base schemas for report serialization.
"""
from marshmallow import Schema, fields, post_load

from testplan.common.serialization import schemas, fields as custom_fields

from .base import Report, ReportGroup


__all__ = [
    'ReportLogSchema',
    'ReportSchema',
    'ReportGroupSchema'
]


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

    source_class = Report

    name = fields.String()
    description = fields.String(allow_none=True)
    entries = fields.List(custom_fields.NativeOrPretty())

    uid = fields.String()
    logs = fields.Nested(ReportLogSchema, many=True)

    @post_load
    def make_report(self, data):
        """Create report object, attach log list."""
        logs = data.pop('logs', [])
        rep = self.get_source_class()(**data)
        rep.logs = logs
        return rep


class ReportGroupSchema(ReportSchema):
    """Schema for ``base.ReportGroup``."""

    source_class = ReportGroup

    entries = custom_fields.GenericNested(
        schema_context={
            'Report': ReportSchema,
            'ReportGroup': 'self'
        },
        many=True
    )
