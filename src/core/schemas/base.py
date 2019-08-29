import json

from marshmallow import Schema, post_load

from django.utils.translation import get_language


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
        return self.to_json()

    def to_dict(self):
        out = {}
        for key in self.__schema__.declared_fields:
            v = getattr(self, key)
            if isinstance(v, GenericModel):
                out[key] = v.to_dict()
            elif isinstance(v, list):
                out[key] = [x.to_dict() for x in v] if v and isinstance(v[0], GenericModel) else v
            elif isinstance(v, (int, float)) or v is None:
                out[key] = v
            else:
                out[key] = str(v)
        return out

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_display(self):
        out = {}
        for key in self.__schema__.declared_fields:
            v = getattr(self, key)
            if v:
                metadata = getattr(self, 'metadata').get(key)
                label = metadata.get('title')
                if isinstance(v, GenericModel):
                    value = v.to_display()
                elif isinstance(v, list):
                    kwargs = {'roles': True} if key == 'contributors' else {}
                    value = [x.to_display(**kwargs) for x in v] if v and isinstance(v[0], GenericModel) else v
                elif isinstance(v, (int, float)):
                    value = v
                else:
                    value = str(v)
                if value:
                    out[key] = {
                        'label': label,
                        'value': value,
                    }
        return out


class BaseSchema(Schema):
    __model__ = GenericModel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contributors_fields = []
        self.locations_fields = []
        for fld in self.declared_fields:
            if (
                fld == 'contributors'
                or self.declared_fields[fld].metadata.get('x-attrs', {}).get('equivalent') == 'contributors'
            ):
                self.contributors_fields.append(fld)
            elif 'location' in fld:
                self.locations_fields.append(fld)

    @post_load
    def create_object(self, data):
        return self.__model__(self, **data)

    def get_model(self, data):
        return self.load(data).data

    def data_display(self, data):
        m = self.get_model(data)
        return m.to_display()

    def role_display(self, data, user_source):
        lang = get_language() or 'en'
        roles = []
        for fld in self.contributors_fields:
            if data.get(fld):
                for c in data[fld]:
                    if c.get('source') == user_source and c.get('roles'):
                        for r in c['roles']:
                            roles.append(r.get('label').get(lang))
        if roles:
            return ', '.join(sorted(set(roles)))

    def location_display(self, data):
        locations = []
        for fld in self.locations_fields:
            if data.get(fld):
                if fld == 'location':
                    for loc in data[fld]:
                        if loc.get('label'):
                            locations.append(loc['label'])
                else:
                    for o in data[fld]:
                        if o.get('location'):
                            for loc in o['location']:
                                if loc.get('label'):
                                    locations.append(loc['label'])
        if locations:
            return ', '.join(sorted(set(locations)))

    def year_display(self, data):
        return None
