import json

from django.conf import settings
from drf_yasg import openapi
from drf_yasg.app_settings import swagger_settings
from drf_yasg.codecs import OpenAPICodecJson
from drf_yasg.inspectors import FieldInspector, NotHandled, SwaggerAutoSchema
from drf_yasg.utils import force_real_str, swagger_auto_schema
from rest_framework import serializers
from rest_framework.utils.encoders import JSONEncoder

from core.schemas import get_keywords_jsonschema, get_texts_jsonschema, get_type_jsonschema

authorization_header_paramter = openapi.Parameter(
    'Authorization',
    openapi.IN_HEADER,
    required=True,
    type=openapi.TYPE_STRING,
)

language_header_parameter = openapi.Parameter(
    'Accept-Language',
    openapi.IN_HEADER,
    required=False,
    type=openapi.TYPE_STRING,
    enum=list(settings.LANGUAGES_DICT.keys()),
)

language_header_decorator = swagger_auto_schema(manual_parameters=[language_header_parameter])


class JSONFieldInspector(FieldInspector):
    def field_to_swagger_object(
            self, field, swagger_object_type, use_references, **kwargs
    ):
        SwaggerType, ChildSwaggerType = self._get_partial_types(field, swagger_object_type, use_references, **kwargs)

        if isinstance(field, serializers.JSONField):
            if field.field_name == 'type':
                return SwaggerType(
                    title=force_real_str(field.label) if field.label else None,
                    type=openapi.TYPE_OBJECT,
                    properties=get_type_jsonschema()['properties'],
                    additionalProperties=False,
                )
            elif field.field_name == 'keywords':
                return SwaggerType(
                    title=force_real_str(field.label) if field.label else None,
                    type=openapi.TYPE_ARRAY,
                    items=get_keywords_jsonschema()['items'],
                )
            elif field.field_name == 'texts':
                return SwaggerType(
                    title=force_real_str(field.label) if field.label else None,
                    type=openapi.TYPE_ARRAY,
                    items=get_texts_jsonschema()['items'],
                )
            return SwaggerType(
                type=openapi.TYPE_OBJECT,
            )

        return NotHandled


class JSONAutoSchema(SwaggerAutoSchema):
    field_inspectors = [JSONFieldInspector] + swagger_settings.DEFAULT_FIELD_INSPECTORS


class OpenAPICodecDRFJson(OpenAPICodecJson):
    def _dump_dict(self, spec):
        """Dump ``spec`` into JSON."""
        return json.dumps(spec, cls=JSONEncoder)
