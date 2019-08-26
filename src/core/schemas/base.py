from marshmallow import Schema, post_load


class GenericModel:
    def __init__(self, schema, **kwargs):
        self.__schema__ = schema
        self.metadata = {}
        for attr in schema.declared_fields:
            self.metadata[attr] = schema.declared_fields[attr].metadata
            if hasattr(schema.declared_fields[attr], 'many'):
                setattr(self, attr, [])
            else:
                setattr(self, attr, None)
        for k, v in kwargs.items():
            if k in schema.declared_fields:
                setattr(self, k, v)

    def __repr__(self):
        return str(self.to_json())

    def to_json(self):
        out = {}
        for key in self.__schema__.declared_fields:
            v = getattr(self, key)
            if isinstance(v, GenericModel):
                out[key] = str(v)
            elif isinstance(v, (int, float)) or v is None:
                out[key] = v
            else:
                out[key] = str(v)
        return out


class BaseSchema(Schema):
    @post_load
    def create_object(self, data):
        return GenericModel(self, **data)
