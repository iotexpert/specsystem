from django.conf import settings
from rest_framework import serializers

from ..models import DocType

class DocTypeSerializer(serializers.ModelSerializer):
    jira_temp_url = serializers.CharField(read_only=True)
    jira_temp_url_base = serializers.CharField(read_only=True)
    class Meta:
        model = DocType
        fields = ('name', 'descr', 'confidential', 'jira_temp', 'sunset_interval', 'sunset_warn', 'active', 'jira_temp_url', 'jira_temp_url_base')

    def to_representation(self, value):
        data = super(DocTypeSerializer, self).to_representation(value)
        if value.jira_temp is not None and len(value.jira_temp) > 0 \
            and settings.JIRA_URI is not None and len(settings.JIRA_URI) > 0:
            data['jira_temp_url'] = f'{settings.JIRA_URI}/browse/{value.jira_temp}'
        if settings.JIRA_URI is not None or len(settings.JIRA_URI) > 0:
            data['jira_temp_url_base'] = f'{settings.JIRA_URI}/browse/'
        return data

class DocTypePutSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocType
        fields = ('descr', 'confidential', 'jira_temp', 'sunset_interval', 'sunset_warn', 'active',  )

    def update(self, doctype, validated_data):
        if not validated_data['sunset_interval']:
            validated_data['sunset_interval'] = None
        if not validated_data['sunset_warn']:
            validated_data['sunset_warn'] = None

        return super(DocTypePutSerializer, self).update(doctype, validated_data)