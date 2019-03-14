from rest_framework import serializers


class CleanModelSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        instance = self.Meta.model(**attrs)
        instance.clean()
        return attrs


class SwaggerMetaModelSerializer(serializers.ModelSerializer):
    @staticmethod
    def _swagger_meta(attrs=None):
        class Meta:
            swagger_schema_fields = {'x-attrs': attrs} if attrs else None

        return Meta

    def __init__(self, **kwargs):
        super(SwaggerMetaModelSerializer, self).__init__(**kwargs)
        if hasattr(self, 'Meta') and hasattr(self.Meta, 'swagger_meta_attrs'):
            for f, attrs in self.Meta.swagger_meta_attrs.items():
                field = self.fields.get(f)
                if field and attrs:
                    if hasattr(field, 'Meta'):
                        setattr(field.Meta, 'swagger_schema_fields', {'x-attrs': attrs})
                    else:
                        setattr(field, 'Meta', self._swagger_meta(attrs=attrs))
