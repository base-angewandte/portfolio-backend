import json
import logging

from apimapper import APIMapper, config as apiconfig
from django.conf import settings
from django.utils.module_loading import import_string
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder

from api.yasg import language_header_parameter
from core.skosmos import autosuggest

logger = logging.getLogger(__name__)

fieldname_paramter = openapi.Parameter(
    'fieldname',
    openapi.IN_PATH,
    required=True,
    type=openapi.TYPE_STRING,
    enum=list(settings.ACTIVE_SOURCES.keys()),
)


@swagger_auto_schema(
    methods=['get'],
    manual_parameters=[fieldname_paramter, language_header_parameter],
    operation_id='autosuggest_v1_lookup_all',
)
@api_view(['GET'])
def lookup_view(request, fieldname, *args, **kwargs):
    source = settings.ACTIVE_SOURCES.get(fieldname, ())

    if isinstance(source, dict):
        source = source.get('all', ())

    if isinstance(source, str):
        data = import_string(source)()
    else:
        data = fetch_responses('', source)

    return Response(data)


@swagger_auto_schema(
    methods=['get'],
    manual_parameters=[fieldname_paramter, language_header_parameter],
    operation_id='autosuggest_v1_lookup',
)
@api_view(['GET'])
def lookup_view_search(request, fieldname, searchstr='', *args, **kwargs):
    source = settings.ACTIVE_SOURCES.get(fieldname, ())

    if isinstance(source, dict):
        source = source.get('search', ())

    if isinstance(source, str):
        data = autosuggest(import_string(source)(), searchstr)
    else:
        data = fetch_responses(searchstr, source)

    return Response(data)


def fetch_responses(querystring, active_sources):
    responses = []
    for src in active_sources:
        api = APIMapper(
            # this is kinda hacky - change it if there's a better solution to force evaluation of lazy objects
            # inside a dict
            json.loads(json.dumps(settings.SOURCES.get(src), cls=JSONEncoder)),
            settings.RESPONSE_MAPS.get(src),
            timeout=2,
        )
        res = api.fetch_results(querystring)
        responses.extend(res)

    return responses
