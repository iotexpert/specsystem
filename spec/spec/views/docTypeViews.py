import re
from django.db import transaction
from proj.util import IsSuperUserOrReadOnly
from rest_framework import status
from rest_framework.decorators import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from spec.views.specViews import genCsv
from utils import qsUtil
from utils.dev_utils import formatError

from ..models import  DocType
from ..serializers.docTypeSerializers import DocTypeSerializer, DocTypePutSerializer

class DocTypeList(APIView):
    """
    get:
    Return list of DocTypes

    post:
    Create DocType

    {
        "name": "WI",
        "descr": "Work Instruction",
        "confidential": false,
        "jira_temp": "",
        "sunset_interval": "1095 00:00:00",
        "sunset_warn": "60 00:00:00"
    }
    """
    permission_classes = [IsSuperUserOrReadOnly]
    def get(self, request, format=None):
        try:
            doc_types = DocType.objects.all()
            doc_types = qsUtil.qsFilter(
                doc_types,
                request.GET,
                ['name', 'descr', 'jira_temp', {"f": "confidential", "t": bool}],
                ["name"],
            )

            # If requested, return the entire data set in a csv file
            if request.GET.get('output_csv'):
                return genCsv(request, 'doc_type_list.csv', DocTypeSerializer(), doc_types)

            pagination = LimitOffsetPagination()
            page = pagination.paginate_queryset(doc_types, request)
            serializer = DocTypeSerializer(page, many=True)
            return pagination.get_paginated_response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DTV01")

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = DocTypeSerializer(data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-DTV03", "error": "Invalid message format", "schemaErrors":serializer.errors})
                if re.search(r'[^-a-zA-Z0-9_:]+',serializer.validated_data["name"]):
                    raise ValidationError({"errorCode":"SPEC-DTV02", "error": "Document Type names cannot contain special characters, including: space, comma, tab, semicolon and slash"})
                doctype = serializer.save()
            serializer = DocTypeSerializer(doctype)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DTV04")


class DocTypeDetail(APIView):
    """
    get:
    doctype/<doctype>
    Return details of specific DocType

    put:
    doctype/<doctype>
    Update <doctype>

    {
        "name": "WI",
        "descr": "Work Instruction",
        "confidential": false,
        "jira_temp": "",
        "sunset_interval": "1096 00:00:00",
        "sunset_warn": "90 00:00:00",
    }

    delete:
    doctype/<doctype>
    Delete specified <doctype> entry
    """
    permission_classes = [IsSuperUserOrReadOnly]
    def get_object(self, doctype):
        try:
            return DocType.objects.get(name=doctype)
        except DocType.DoesNotExist:
            raise ValidationError({"errorCode":"SPEC-DTV05", "error": f"DocType ({doctype}) does not exist."})

    def get(self, request, doctype, format=None):
        try:
            doctype = self.get_object(doctype)
            serializer = DocTypeSerializer(doctype)
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DTV06")

    def put(self, request, doctype, format=None):
        try:
            with transaction.atomic():
                doctype = self.get_object(doctype)
                serializer = DocTypePutSerializer(doctype, data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-DTV07", "error": "Invalid message format", "schemaErrors":serializer.errors})
                doctype = serializer.save()
            serializer = DocTypeSerializer(doctype)
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DTV08")

    def delete(self, request, doctype, format=None):
        try:
            with transaction.atomic():
                doctype = self.get_object(doctype)
                doctype.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DTV09")
