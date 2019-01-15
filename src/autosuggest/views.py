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
    data = fetch_responses(settings.PERSON_URLS, searchstr)

    return Response(data)


@api_view(['GET'])
def lookup_place_view(request, *args, **kwargs):
    searchstr = kwargs.get('searchstr')
    return Response([{"id": '1',
                      "label": searchstr,
                      'source': 'GND'},
                     {"id": '1',
                      "label": searchstr,
                      'source': 'GND'}    ])


def fetch_responses(url_dict, querystring):
    responses = []
    with FuturesSession() as session:
        fetch_requests = {domain: session.get(url+querystring) for domain, url in url_dict.items()}
        for domain, req in fetch_requests.items():
            if status.is_success(req.result().status_code):
                result_field = settings.RESULT.get(domain)
                result_json = json.loads(req.result().content).get(result_field) if result_field else json.loads(req.result().content)
                responses.extend(map_to_common_schema(result_json, domain))
                
        
    return responses


def map_to_common_schema(response_content, domain):
    data = []
    mapping = settings.MAPPING.get(domain)
    for suggestion in response_content:
        mapped_schema = {to_key: suggestion.get(from_key) for to_key, from_key in mapping.items()}
        data.append(mapped_schema)
        
    return data
