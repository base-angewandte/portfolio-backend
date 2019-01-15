from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets

# Create your views here.
'''
class PersonViewSet(viewsets.ViewSet):
    @api_view(['GET'])
    def lookup_person_view(request, searchstring, *args, **kwargs):
        print('ARGS', args, 'KWARGS', kwargs, 'SEARCHSTRING', searchstring)
        return Response({"id": '1',
                         "label": 'Garibaldi',
                         'source': 'GND'})
'''

@api_view(['GET'])
def lookup_person_view(request, *args, **kwargs):
    print('ARGS', args, 'KWARGS', kwargs)
    print('request', request.GET)
    return Response({"id": '1',
                     "label": 'Garibaldi',
                     'source': 'GND'})

@api_view(['GET'])
def lookup_place_view(request, *args, **kwargs):
    print('ARGS', args, 'KWARGS', kwargs)
    return Response({"id": '1',
                     "label": 'Milano',
                     'source': 'GND'})
