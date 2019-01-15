from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets

# Create your views here.
@api_view(['GET'])
def lookup_person_view(request, *args, **kwargs):
    searchstr = kwargs.get('searchstr')
    return Response({"id": '1',
                     "label": searchstr,
                     'source': 'GND'})

@api_view(['GET'])
def lookup_place_view(request, *args, **kwargs):
    searchstr = kwargs.get('searchstr')
    return Response({"id": '1',
                     "label": searchstr,
                     'source': 'GND'})
