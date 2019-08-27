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


class BaseSchema(Schema):
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
            elif (
                'location' in fld
                or self.declared_fields[fld].metadata.get('x-attrs', {}).get('locations_info')
            ):
                self.locations_fields.append(fld)

    @post_load
    def create_object(self, data):
        return GenericModel(self, **data)

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
