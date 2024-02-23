
from rest_framework import serializers

from ..models import Location

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('name', 'active', )

class LocationPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('name', 'active', )

class LocationPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('active', )
