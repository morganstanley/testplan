"""
Base classes / logic for marshalling go here.
"""
from marshmallow import Schema, fields
from testplan.common.serialization import fields as custom_fields


from testplan.common.serialization.schemas import SchemaRegistry
from .. import base


class AssertionSchemaRegistry(SchemaRegistry):
    def get_category(self, obj):
        return obj.meta_type


registry = AssertionSchemaRegistry()


class GenericEntryList(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return [registry.serialize(entry) for entry in value]


@registry.bind_default()
class BaseSchema(Schema):
    utc_time = custom_fields.UTCDateTime()
    machine_time = custom_fields.LocalDateTime()
    type = custom_fields.ClassName()
    meta_type = fields.String()
    description = custom_fields.Unicode()
    line_no = fields.Integer()
    category = fields.String()
    flag = fields.String()
    file_path = fields.String()
    custom_style = fields.Dict(keys=fields.String(), values=fields.String())

    def load(self, *args, **kwargs):
        raise NotImplementedError("Only serialization is supported.")


@registry.bind(base.Group, base.Summary)
class GroupSchema(Schema):
    type = custom_fields.ClassName()
    utc_time = custom_fields.UTCDateTime()
    passed = fields.Boolean()
    meta_type = fields.String()
    description = custom_fields.Unicode(allow_none=True)
    entries = GenericEntryList(allow_none=True)


@registry.bind(base.Log)
class LogSchema(BaseSchema):
    message = fields.Raw()


@registry.bind(base.CodeLog)
class CodeLogSchema(BaseSchema):
    code = fields.String()
    language = fields.String()


@registry.bind(base.Markdown)
class MarkdownSchema(BaseSchema):
    message = fields.String()
    escape = fields.Boolean()


@registry.bind(base.TableLog)
class TableLogSchema(BaseSchema):
    table = fields.List(fields.List(custom_fields.NativeOrPretty()))
    indices = fields.List(fields.Integer(), allow_none=True)
    display_index = fields.Boolean()
    columns = fields.List(fields.String(), allow_none=False)


@registry.bind(base.DictLog, base.FixLog)
class DictLogSchema(BaseSchema):
    flattened_dict = fields.Raw()


@registry.bind(base.Graph)
class GraphSchema(BaseSchema):
    graph_type = fields.String()
    graph_data = fields.Dict(
        keys=fields.String(), values=fields.List(fields.Dict())
    )
    series_options = fields.Dict(
        keys=fields.String(), values=fields.Dict(), allow_none=True
    )
    type = fields.String()
    graph_options = fields.Dict(allow_none=True)
    discrete_chart = fields.Bool()


@registry.bind(base.Attachment, base.MatPlot)
class AttachmentSchema(BaseSchema):
    source_path = fields.String()
    orig_filename = fields.String()
    filesize = fields.Integer()
    dst_path = fields.String()


@registry.bind(base.Plotly)
class PlotlySchema(AttachmentSchema):
    style = fields.Dict(allow_none=True)


@registry.bind(base.Directory)
class DirectorySchema(BaseSchema):
    source_path = fields.String()
    dst_path = fields.String()
    ignore = fields.List(fields.String(), allow_none=True)
    only = fields.List(fields.String(), allow_none=True)
    recursive = fields.Boolean()
    file_list = fields.List(fields.String())
