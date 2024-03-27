import re
from wsgiref import validate
from rest_framework import serializers

from ..models import ApprovalMatrix, ApprovalMatrixSignRole, Department, DepartmentReadRole, DocType, Role

class ApprovalMatrixSerializer(serializers.ModelSerializer):
    signRoles = serializers.StringRelatedField(many=True)
    class Meta:
        model = ApprovalMatrix
        fields = ('id', 'doc_type', 'department', 'signRoles', )

    def to_representation(self, value):
        data = super(ApprovalMatrixSerializer, self).to_representation(value)
        data['signRoles'] = ', '.join(sorted(data['signRoles']))
        return data

class ApprovalMatrixPostSerializer(serializers.ModelSerializer):
    doc_type = serializers.CharField(required=False)
    department = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    signRoles = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    class Meta:
        model = ApprovalMatrix
        fields = ('id', 'doc_type', 'department', 'signRoles',  )

    def create(self, validated_data):
        sign_role_data = validated_data.pop("signRoles")
        validated_data['doc_type'] = DocType.lookup(validated_data['doc_type'])
        if validated_data['department']:
            validated_data['department'] = Department.lookup(validated_data['department'])
        apvl_mt = ApprovalMatrix.objects.create(**validated_data)

        if sign_role_data:
            roles = re.split(r"[\s;,]+",sign_role_data)
            for role in roles:
                _role = Role.lookup(role)
                _signRole = ApprovalMatrixSignRole.objects.create(apvl_mt=apvl_mt,role=_role)

        return apvl_mt

class ApprovalMatrixUpdateSerializer(serializers.ModelSerializer):
    doc_type = serializers.CharField(required=False)
    department = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    signRoles = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    class Meta:
        model = ApprovalMatrix
        fields = ('id', 'doc_type', 'department', 'signRoles',  )

    def update(self, apvl_mt, validated_data):
        sign_role_data = validated_data.pop("signRoles")
        validated_data['doc_type'] = DocType.lookup(validated_data['doc_type'])
        if validated_data['department']:
            validated_data['department'] = Department.lookup(validated_data['department'])

        ApprovalMatrixSignRole.objects.filter(apvl_mt=apvl_mt).delete()
        if sign_role_data:
            roles = re.split(r"[\s;,]+",sign_role_data)
            for role in roles:
                _role = Role.lookup(role)
                _signRole = ApprovalMatrixSignRole.objects.create(apvl_mt=apvl_mt,role=_role)

        return apvl_mt
