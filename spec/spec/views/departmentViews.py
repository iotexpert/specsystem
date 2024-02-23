import collections.abc
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

from ..models import  Department
from ..serializers.departmentSerializers import DepartmentSerializer, DepartmentPostSerializer, DepartmentUpdateSerializer

class DepartmentList(APIView):
    """
    get:
    Return list of departments

    post:
    Create department

    {
        "name": "DOC_MGR",
        "roles": "role1, role2"
    }
    """
    permission_classes = [IsSuperUserOrReadOnly]
    def get(self, request, format=None):
        try:
            depts = Department.objects.all()
            depts = qsUtil.qsFilter(
                depts,
                request.GET,
                ['name', {"f": "active", "t": bool}, ],
                ["name"],
            )

            # If requested, return the entire data set in a csv file
            if request.GET.get('output_csv'):
                return genCsv(request, 'dept_list.csv', DepartmentSerializer(), depts)

            pagination = LimitOffsetPagination()
            page = pagination.paginate_queryset(depts, request)
            serializer = DepartmentSerializer(page, many=True)
            return pagination.get_paginated_response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DV01")

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                req = request.data
                if not isinstance(req, collections.abc.Sequence):
                    req = [req]
                for r in req:
                    department = None
                    if 'name' in r:
                        department = Department.objects.filter(name=r['name']).first()
                    if department:
                        serializer = DepartmentUpdateSerializer(department, data=r)
                    else:
                        serializer = DepartmentPostSerializer(department, data=r)
                    if not serializer.is_valid():
                        raise ValidationError({"errorCode":"SPEC-DV03", "error": "Invalid message format", "schemaErrors":serializer.errors})
                    if re.search(r'[^-a-zA-Z0-9_:]+',r["name"]):
                        raise ValidationError({"errorCode":"SPEC-DV02", "error": "Department names cannot contain special characters, including: space, comma, tab, semicolon and slash"})
                    department = serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DV04")


class DepartmentDetail(APIView):
    """
    get:
    department/<dept>
    Return details of specific department

    put:
    department/<dept>
    Update <department> with new roles

    {
        "roles": "role1, role3"
    }

    delete:
    department/<dept>
    Delete specified <department> entry
    """
    permission_classes = [IsSuperUserOrReadOnly]
    def get_object(self, dept):
        try:
            return Department.objects.get(name=dept)
        except Department.DoesNotExist:
            raise ValidationError({"errorCode":"SPEC-DV05", "error": f"Department ({dept}) does not exist."})

    def get(self, request, dept, format=None):
        try:
            department = self.get_object(dept)
            serializer = DepartmentSerializer(department)
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DV06")

    def put(self, request, dept, format=None):
        try:
            with transaction.atomic():
                department = self.get_object(dept)
                serializer = DepartmentUpdateSerializer(department, data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-DV07", "error": "Invalid message format", "schemaErrors":serializer.errors})
                serializer.save()
            serializer = DepartmentSerializer(department)
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DV08")

    def delete(self, request, dept, format=None):
        try:
            with transaction.atomic():
                department = self.get_object(dept)
                department.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DV09")
