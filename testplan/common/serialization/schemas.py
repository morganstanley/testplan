from marshmallow import Schema

from testplan.common.utils.registry import Registry

from . import fields as custom_fields


def load_tree_data(
    data,
    node_schema,
    leaf_schema,
    nodes_field="entries",
    nodes_attr_name="entries",
    type_field="type",
):
    """
    marshmallow does not support tree serialization with different
    node types, so we rely on this recursive function for traversing
    tree data and instantiate node objects with the given schemas.
    """

    node_type = node_schema.get_source_class().__name__
    leaf_type = leaf_schema.get_source_class().__name__

    def _load(_data):
        obj_type = _data.pop(type_field)

        if obj_type == node_type:
            child_data = _data.pop(nodes_field)
            obj = node_schema().load(_data)
            nodes = [_load(c_data) for c_data in child_data]
            setattr(obj, nodes_attr_name, nodes)
            return obj

        elif obj_type == leaf_type:
            return leaf_schema().load(_data)
        else:
            raise ValueError("Invalid object type: {}".format(obj_type))

    return _load(data)


class TreeNodeSchema(Schema):
    """
    Base class that can be used for defining
    tree node schemas, compatible with `load_tree_data`.
    """

    source_class = None
    type = custom_fields.ClassName()

    @classmethod
    def get_source_class(cls):
        """Wrapper around class level attribute to support inheritance."""
        if not cls.source_class:
            raise ValueError("`source_class` attribute is not set")
        return cls.source_class


class SchemaRegistry(Registry):
    """
    Registry class to be used with Marshmallow schemas, provides
    `serialize` method that calls `dump` on the underlying schema mapping.
    """

    def serialize(self, obj):
        return self[obj]().dump(obj)
