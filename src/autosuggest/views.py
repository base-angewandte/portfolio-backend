from django.conf import settings
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets
import json

from requests_futures.sessions import FuturesSession
from rest_framework import status

# Create your views here.
@api_view(['GET'])
def lookup_person_view(request, *args, **kwargs):
    searchstr = kwargs.get('searchstr')
    data = fetch_responses(searchstr,
                           settings.ACTIVE_SOURCES.get('PERSON'))

    return Response(data)


@api_view(['GET'])
def lookup_place_view(request, *args, **kwargs):
    searchstr = kwargs.get('searchstr')
    data = fetch_responses(searchstr,
                           settings.ACTIVE_SOURCES.get('PLACE'))

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
                mapped_schema['resource_id'] = '{}{}'.format(domain_dict.get('resourceid_prefix', ''), mapped_schema.get('_id'))
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
                fetch_requests[domain] = session.get(val.get('url')+querystring)
                
        for domain, req in fetch_requests.items():
            domain_dict = settings.LOOKUP.get(domain)
            if status.is_success(req.result().status_code):
                result_field = domain_dict.get('result')
                try:        
                    if result_field:
                        result_json = json.loads(req.result().content).get(result_field)
                    else:
                        result_json = json.loads(req.result().content)
                        
                except json.JSONDecodeError as e:
                    # probably 500 - result content is not in a json decodable format
                    # TODO: Use the correct logging handler and log
                    print(repr(e), req.result().content)
                    continue
                
                if result_json and len(result_json):
                    mapped_data = map_to_common_schema(result_json, domain_dict)
                    responses.extend(mapped_data)
                else:
                    pass
            else:
                # TODO: log don't print
                print('---------------Not a sucess', req.result().status_code)
                print(req.result().content)
    return responses


