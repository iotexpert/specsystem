import re
from user.models import User
from rest_framework import serializers

from ..models import Department, DepartmentReadRole, Role

class DepartmentSerializer(serializers.ModelSerializer):
    readRoles = serializers.StringRelatedField(many=True)
    class Meta:
        model = Department
        fields = ('name', 'readRoles', 'active', )

    def to_representation(self, value):
        data = super(DepartmentSerializer, self).to_representation(value)
        data['readRoles'] = ', '.join(sorted(data['readRoles']))
        return data

class DepartmentPostSerializer(serializers.ModelSerializer):
    readRoles = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    class Meta:
        model = Department
        fields = ('name', 'readRoles', 'active', )

    def create(self, validated_data):
        readRoles_data = validated_data.pop("readRoles")
        dept = Department.objects.create(**validated_data)
        if readRoles_data:
            roles = re.split(r"[\s;,]+",readRoles_data)
            for roleName in roles:
                role = Role.lookup(roleName)
                deptReadRole = DepartmentReadRole.objects.create(dept=dept,role=role)
        return dept

class DepartmentUpdateSerializer(serializers.Serializer):
    readRoles = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    active = serializers.BooleanField()

    def update(self, dept, validated_data):
        dept.active = validated_data.pop("active")
        dept.save()

        readRoles_data = validated_data.pop("readRoles")
        DepartmentReadRole.objects.filter(dept=dept).delete()
        if readRoles_data:
            roles = re.split(r"[\s;,]+",readRoles_data)
            for roleName in roles:
                role = Role.lookup(roleName)
                deptReadRole = DepartmentReadRole.objects.create(dept=dept,role=role)
        return dept
