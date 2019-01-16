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
    data = fetch_responses(settings.LOOKUP.get('PERSON'), searchstr)

    return Response(data)


@api_view(['GET'])
def lookup_place_view(request, *args, **kwargs):
    searchstr = kwargs.get('searchstr')
    data = fetch_responses(settings.LOOKUP.get('PLACE'), searchstr)

    return Response(data)


def fetch_responses(lookup_dict, querystring):
    responses = []
    with FuturesSession() as session:
        fetch_requests = {domain: session.get(val.get('url')+querystring) for domain, val in lookup_dict.items() if domain in settings.ACTIVE_SOURCES}
        for domain, req in fetch_requests.items():
            if status.is_success(req.result().status_code):
                result_field = lookup_dict.get(domain).get('result')
                result_json = json.loads(req.result().content).get(result_field) if result_field else json.loads(req.result().content)
                if result_json and len(result_json):
                    mapped_data = map_to_common_schema(result_json, lookup_dict.get(domain))
                    responses.extend(mapped_data)
                
        
    return responses


def map_to_common_schema(response_content, domain_dict):
    data = []
    
    mapping = domain_dict.get('mapping')
    for suggestion in response_content:
        if ((not domain_dict.get('filter')) or
            (domain_dict.get('filter') and all(suggestion.get(filter_field)==filter_value for filter_field, filter_value in domain_dict.get('filter').items()))):            
            mapped_schema = {to_key: suggestion.get(from_key) for to_key, from_key in mapping.items()}
            mapped_schema['resource_id'] = '{}{}'.format(domain_dict.get('resourceid_prefix', ''), mapped_schema.get('_id'))
            data.append(mapped_schema)

        
        
    return data
