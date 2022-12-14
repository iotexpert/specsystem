import re
from user.models import User
from rest_framework import serializers

from ..models import Role, RoleUser

class RoleSerializer(serializers.ModelSerializer):
    users = serializers.StringRelatedField(many=True)
    class Meta:
        model = Role
        fields = ('role', 'descr', 'spec_one', 'users', )

    def to_representation(self, value):
        data = super(RoleSerializer, self).to_representation(value)
        data['users'] = ', '.join(sorted(data['users']))
        data['user_arr'] = []
        for roleUser in value.users.all():
            data['user_arr'].append({
                "username":roleUser.user.username,
                "email":roleUser.user.email,
                "first_name":roleUser.user.first_name,
                "last_name":roleUser.user.last_name
            })
        return data

class RolePostSerializer(serializers.ModelSerializer):
    users = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    class Meta:
        model = Role
        fields = ('role', 'descr', 'spec_one', 'users', )
    
    def create(self, validated_data):
        role_user_data = validated_data.pop("users")
        role = Role.objects.create(**validated_data)
        if role_user_data:
            users = re.split(r"[\s:;,]+",role_user_data)
            for role_user in users:
                user = User.lookup(username=role_user)
                role_user = RoleUser.objects.create(role=role,user=user)
        
        # If the user list is empty, the user must specify a person on the spec
        if role.users.count() == 0:
            role.spec_one = True
            role.save()
            
        return role

class RoleUpdateSerializer(serializers.Serializer):
    descr = serializers.CharField(allow_null=True)
    spec_one = serializers.BooleanField()
    users = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    
    def update(self, role, validated_data):
        role.descr = validated_data["descr"]
        role.spec_one = validated_data["spec_one"]
        role.save()

        RoleUser.objects.filter(role=role).delete()                    
        users = re.split(r"[\s:;,]+", validated_data["users"])
        for username in users:
            if len(username) > 0:
                user = User.lookup(username=username)
                role_user = RoleUser.objects.create(role=role, user=user)
        
        # If the user list is empty, the user must specify a person on the spec
        if role.users.count() == 0:
            role.spec_one = True
            role.save()

        return role


