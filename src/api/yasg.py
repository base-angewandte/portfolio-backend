from drf_yasg import openapi
from drf_yasg.app_settings import swagger_settings
from drf_yasg.inspectors import FieldInspector, NotHandled, SwaggerAutoSchema
from rest_framework import serializers

from core.schemas import get_texts_jsonschema, get_keywords_jsonschema


class JSONFieldInspector(FieldInspector):
    def field_to_swagger_object(
            self, field, swagger_object_type, use_references, **kwargs
    ):
        SwaggerType, ChildSwaggerType = self._get_partial_types(field, swagger_object_type, use_references, **kwargs)

        if isinstance(field, serializers.JSONField):
            if field.field_name == 'keywords':
                return SwaggerType(
                    type=openapi.TYPE_ARRAY,
                    items=get_keywords_jsonschema()['items'],
                )
            elif field.field_name == 'texts':
                return SwaggerType(
                    type=openapi.TYPE_ARRAY,
                    items=get_texts_jsonschema()['items'],
                )
            return SwaggerType(
                type=openapi.TYPE_OBJECT,
            )

        return NotHandled


class JSONAutoSchema(SwaggerAutoSchema):
    field_inspectors = [JSONFieldInspector] + swagger_settings.DEFAULT_FIELD_INSPECTORS


class UserOperationIDAutoSchema(SwaggerAutoSchema):
    def get_operation_id(self, operation_keys):
        operation_id = super(UserOperationIDAutoSchema, self).get_operation_id(operation_keys)
        return operation_id.replace('list', 'read')
