import re
from django.db import transaction
from proj.util import IsSuperUserOrReadOnly
from rest_framework import status
from rest_framework.decorators import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from spec.views.specViews import genCsv
from utils.dev_utils import formatError

from ..models import  Location
from ..serializers.locationSerializers import LocationSerializer, LocationPostSerializer

class LocationList(GenericAPIView):
    """
    get:
    Return list of locations

    post:
    Create location

    {
        "name": "Corporate"
    }
    """
    permission_classes = [IsSuperUserOrReadOnly]
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    search_fields = ('name', )

    def get(self, request, format=None):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            queryset = self.paginate_queryset(queryset.order_by('name'))

            serializer = LocationSerializer(queryset, many=True)

            # If requested, return the entire data set in a csv file
            if request.GET.get('output_csv'):
                return genCsv(request, 'loc_list.csv', LocationSerializer(), queryset)

            return self.get_paginated_response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-LC01")

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = LocationPostSerializer(data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-LC03", "error": "Invalid message format", "schemaErrors":serializer.errors})
                if re.search(r'[^-a-zA-Z0-9_: ,]+',serializer.validated_data["name"]):
                    raise ValidationError({"errorCode":"SPEC-LC02", "error": "Location names cannot contain special characters, including: tab, semicolon and slash"})
                location = serializer.save()
            serializer = LocationSerializer(location)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-LC04")


class LocationDetail(APIView):
    """
    get:
    loc/<loc>
    Return details of specific location

    delete:
    loc/<loc>
    Delete specified <loc> entry
    """
    permission_classes = [IsSuperUserOrReadOnly]
    def get(self, request, loc, format=None):
        try:
            location = Location.lookup(loc)
            serializer = LocationSerializer(location)
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-LC06")

    def delete(self, request, loc, format=None):
        try:
            with transaction.atomic():
                location = Location.lookup(loc)
                location.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-LC09")
