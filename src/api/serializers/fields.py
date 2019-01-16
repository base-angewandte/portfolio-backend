def SwaggerSerializerField(cls, attrs=None, *args, **kwargs):
    class Field(cls):
        class Meta:
            swagger_schema_fields = {'x-attrs': attrs} if attrs else None

        def __init__(self):
            super(Field, self).__init__(*args, **kwargs)

    return Field()
