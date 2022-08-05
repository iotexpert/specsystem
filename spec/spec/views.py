import re
from django.db import transaction
from proj.util import IsSuperUserOrReadOnly
from rest_framework import status
from rest_framework.decorators import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from utils.dev_utils import formatError

from user.models import User
from .models import Category, CategoryRole, Role, RoleUser
from .serializers import CategorySerializer, CategoryPostSerializer, CategoryUpdateSerializer, RoleSerializer, RolePostSerializer, RoleUpdateSerializer

class RoleList(GenericAPIView):
    """ 
    get:
    Return list of roles

    post:
    Create role

    {
        "role": "DOC_MGR",
        "descr": "Document control manager",
        "users": "user1, user2"
    }
    """
    permission_classes = [IsSuperUserOrReadOnly]
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    search_fields = ('role','descr')

    def get(self, request, format=None):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            queryset = self.paginate_queryset(queryset.order_by('role'))
            
            serializer = RoleSerializer(queryset, many=True)
            return self.get_paginated_response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-V01")

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                if re.search('[\s|\,|\t|\;|\:]+',request.data["role"]):
                    raise ValidationError({"errorCode":"SPEC-V17", "error": "Role names cannot contain special characters, including: space, comma, tab, semicolon and colon"})
                serializer = RolePostSerializer(data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-V02", "error": "Invalid message format", "schemaErrors":serializer.errors})
                role = serializer.save()
            serializer = RoleSerializer(role)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-V03")


class RoleDetail(APIView):
    """
    get:
    role/<role>
    Return details of specific role

    put:
    role/<role>
    Update <role> with new description or users

    {
        "descr": "Document control manager",
        "users": "user1, user3"
    }

    delete:
    role/<role>
    Delete specified <role> entry
    """
    permission_classes = [IsSuperUserOrReadOnly]
    def get_object(self, role):
        try:
            return Role.objects.get(role=role)
        except Role.DoesNotExist:
            raise ValidationError({"errorCode":"SPEC-V04", "error": f"Role ({role}) does not exist."})

    def get(self, request, role, format=None):
        try:
            role = self.get_object(role)
            serializer = RoleSerializer(role)
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-V05")

    def put(self, request, role, format=None):
        try:
            with transaction.atomic():
                role = self.get_object(role)
                serializer = RoleUpdateSerializer(role, data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-V06", "error": "Invalid message format", "schemaErrors":serializer.errors})
                if serializer.validated_data["descr"]:
                    role.descr = serializer.validated_data["descr"]
                if serializer.validated_data["any"]:
                    role.any = serializer.validated_data["any"]
                if serializer.validated_data["users"]:
                    RoleUser.objects.filter(role=role).delete()
                    
                    users = re.split('[\s|\,|\t|\;|\:]+',serializer.validated_data["users"])
                    for username in users:
                        user = User.lookup(username=username)
                        role_user = RoleUser.objects.create(role=role, user=user)
                role.save()    
            serializer = RoleSerializer(role)
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-V07")

    def delete(self, request, role, format=None):
        try:
            with transaction.atomic():
                role = self.get_object(role)
                role.delete()
            return Response(status=status.HTTP_204_NO_CONTENT) 
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-V08")

class CategoryList(GenericAPIView):
    """ 
    get:
    category/
    category/<cat>
    Return list of categories

    post:
    Create category

    {
        "cat": "IT",
        "sub_cat": "Requirements",
        "descr": "Software Requirements",
        "active": true,
        "confidential": false,
        "file_temp": "",
        "jira_temp": "",
        "roles": ["IT Manager"]
    }
    """
    permission_classes = [IsSuperUserOrReadOnly]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ('cat','sub_cat','descr')

    def get(self, request, cat=None, format=None):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            if cat is not None:
                queryset = queryset.filter(cat=cat)
            queryset = self.paginate_queryset(queryset.order_by('cat', 'sub_cat'))
            
            serializer = CategorySerializer(queryset, many=True)
            return self.get_paginated_response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-V09")

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = CategoryPostSerializer(data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-V10", "error": "Invalid message format", "schemaErrors":serializer.errors})
                category = serializer.save()
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-V11")


class CategoryDetail(APIView):
    """
    get:
    category/<cat>/<sub_cat>
    Return details of specific category / sub-category

    put:
    category/<cat>/<sub_cat>
    Update category / sub-category with new description or roles

    {
        "cat": "HR",
        "sub_cat": "IT",
        "descr": "Software Requirements",
        "active": true,
        "confidential": false,
        "file_temp": "",
        "jira_temp": "",
        "roles": "IT Manager, IT VP"]
    }

    delete:
    category/<cat>/<sub_cat>
    Delete specified category / sub-category entry
    """
    permission_classes = [IsSuperUserOrReadOnly]
    def get_object(self, cat, sub_cat):
        try:
            return Category.objects.get(cat=cat, sub_cat=sub_cat)
        except Category.DoesNotExist:
            raise ValidationError({"errorCode":"SPEC-V12", "error": f"Category ({cat}/{sub_cat}) does not exist."})

    def get(self, request, cat, sub_cat, format=None):
        try:
            cat = self.get_object(cat, sub_cat)
            serializer = CategorySerializer(cat)
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-V13")

    def put(self, request, cat, sub_cat, format=None):
        try:
            with transaction.atomic():
                cat = self.get_object(cat, sub_cat)
                serializer = CategoryUpdateSerializer(cat, data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-V14", "error": "Invalid message format", "schemaErrors":serializer.errors})
                if serializer.validated_data["cat"]:
                    cat.cat = serializer.validated_data["cat"]
                if serializer.validated_data["sub_cat"]:
                    cat.sub_cat = serializer.validated_data["sub_cat"]
                if serializer.validated_data["descr"]:
                    cat.descr = serializer.validated_data["descr"]
                if serializer.validated_data["active"] is not None:
                    cat.active = serializer.validated_data["active"]
                if serializer.validated_data["confidential"] is not None:
                    cat.confidential = serializer.validated_data["confidential"]
                if serializer.validated_data["file_temp"]:
                    cat.file_temp = serializer.validated_data["file_temp"]
                if serializer.validated_data["jira_temp"]:
                    cat.jira_temp = serializer.validated_data["jira_temp"]
                if serializer.validated_data["roles"]:
                    CategoryRole.objects.filter(cat=cat).delete()
                    roles = re.split('[\s|\,|\t|\;|\:]+',serializer.validated_data["roles"])
                    for rolename in roles:
                        role = Role.lookup(roleName=rolename)
                        CategoryRole.objects.filter(cat=cat, role_id=rolename).delete() # Prevent duplicates
                        category_role = CategoryRole.objects.create(cat=cat, role=role)
                cat.save()

            serializer = CategorySerializer(cat)
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-V15")

    def delete(self, request, cat, sub_cat, format=None):
        try:
            with transaction.atomic():
                cat = self.get_object(cat, sub_cat)
                cat.delete()
            return Response(status=status.HTTP_204_NO_CONTENT) 
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-V16")
