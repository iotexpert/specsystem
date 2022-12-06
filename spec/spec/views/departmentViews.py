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

from ..models import  Department
from ..serializers.departmentSerializers import DepartmentSerializer, DepartmentPostSerializer, DepartmentUpdateSerializer

class DepartmentList(GenericAPIView):
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
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    search_fields = ('name', )

    def get(self, request, format=None):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            queryset = self.paginate_queryset(queryset.order_by('name'))
            
            serializer = DepartmentSerializer(queryset, many=True)

            # If requested, return the entire data set in a csv file
            if request.GET.get('output_csv'):
                serializer = DepartmentSerializer(queryset, many=True, context={'user':request.user})
                return genCsv(request, 'dept_list.csv', serializer.data)

            return self.get_paginated_response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-DV01")

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = DepartmentPostSerializer(data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-DV03", "error": "Invalid message format", "schemaErrors":serializer.errors})
                if re.search(r'[^-a-zA-Z0-9_:]+',serializer.validated_data["name"]):
                    raise ValidationError({"errorCode":"SPEC-DV02", "error": "Department names cannot contain special characters, including: space, comma, tab, semicolon and slash"})
                department = serializer.save()
            serializer = DepartmentSerializer(department)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
