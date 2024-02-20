import re
from django.db import transaction
from proj.util import IsSuperUserOrReadOnly
from rest_framework import status
from rest_framework.decorators import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from spec.views.specViews import genCsv
from utils import qsUtil
from utils.dev_utils import formatError

from ..models import  Location
from ..serializers.locationSerializers import LocationPutSerializer, LocationSerializer, LocationPostSerializer

class LocationList(APIView):
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
    def get(self, request, format=None):
        try:
            locations = Location.objects.all()
            locations = qsUtil.qsFilter(
                locations,
                request.GET,
                ['name', {"f": "active", "t": bool}, ],
                ["name"],
            )

            # If requested, return the entire data set in a csv file
            if request.GET.get('output_csv'):
                return genCsv(request, 'loc_list.csv', LocationSerializer(), locations)

            pagination = LimitOffsetPagination()
            page = pagination.paginate_queryset(locations, request)
            serializer = LocationSerializer(page, many=True)
            return pagination.get_paginated_response(serializer.data)
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

    put:
    loc/<loc>
    Update <loc>

    {
        "roles": "role1, role3"
    }

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

    def put(self, request, loc, format=None):
        try:
            with transaction.atomic():
                location = Location.lookup(loc)
                serializer = LocationPutSerializer(location, data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-DTV07", "error": "Invalid message format", "schemaErrors":serializer.errors})
                location = serializer.save()
            serializer = LocationSerializer(location)
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DTV08")

    def delete(self, request, loc, format=None):
        try:
            with transaction.atomic():
                location = Location.lookup(loc)
                location.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-LC09")
