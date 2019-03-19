import json
import logging

from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from requests_futures.sessions import FuturesSession
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@swagger_auto_schema(methods=['get'], operation_id="autosuggest_v1_lookup_all")
@api_view(['GET'])
def lookup_view(request, fieldname, *args, **kwargs):
    # TODO: Configure to return all for some "fieldname"s
    return Response([])


@swagger_auto_schema(methods=['get'], operation_id="autosuggest_v1_lookup")
@api_view(['GET'])
def lookup_view_search(request, fieldname, searchstr='', *args, **kwargs):
    data = fetch_responses(searchstr,
                           settings.ACTIVE_SOURCES.get(fieldname, ()))

    return Response(data)


def fetch_responses(querystring, active_sources):
    def map_to_common_schema(response_content, domain_dict):
        data = []    
        mapping = domain_dict.get('mapping')
        for suggestion in response_content:
            if ((not domain_dict.get('filter')) or
                (domain_dict.get('filter') and
                 all(suggestion.get(filter_field)==filter_value for filter_field, filter_value in domain_dict.get('filter').items()))):            
                mapped_schema = {to_key: suggestion.get(from_key) for to_key, from_key in mapping.items()}
                mapped_schema['source'] = '{}{}'.format(domain_dict.get('resourceid_prefix') or '', mapped_schema.get('source'))
                # not mapped from response but from config
                mapped_schema['source_name'] =domain_dict.get('source_name')
                data.append(mapped_schema)
        
            else:
                pass
            
        return data

    responses = []
    with FuturesSession() as session:
        fetch_requests = {}
        for domain, val in settings.LOOKUP.items():
            if domain in active_sources:
                payload = val.get('payload') or {}
                if val.get('payload_query_field'):
                    payload[val.get('payload_query_field')] = querystring
                fetch_requests[domain] = session.get(val.get('url'), params=payload)
                
        for domain, req in fetch_requests.items():
            domain_dict = settings.LOOKUP.get(domain)
            try:
                result = req.result()
            except Exception as e:
                logger.error('Error while reading result(): %s', repr(e))
                continue
            
            if not status.is_success(result.status_code):
                logger.error('Request to %s failed with error code %s', domain, result.status_code)
                logger.error('Response  content: %s', result.content)
                
            result_field = domain_dict.get('result')
            try:        
                if result_field:
                    result_json = json.loads(result.content).get(result_field)
                else:
                    result_json = json.loads(result.content)
                    
            except json.JSONDecodeError as e:
                # probably 500 - result content is not in a json decodable format
                logger.error('Exception %s occured while decoding response: %s', repr(e), result.content)
                continue
                
            if result_json and len(result_json):
                mapped_data = map_to_common_schema(result_json, domain_dict)
                responses.extend(mapped_data)
            else:
                pass


    return responses


