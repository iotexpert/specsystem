from django.conf import settings
from rest_framework import serializers

from ..models import Spec, SpecFile, SpecHist, SpecReference, SpecSig


class ImportSpecSerializer(serializers.Serializer):
    num = serializers.IntegerField()
    ver = serializers.CharField()
    state = serializers.CharField()
    title = serializers.CharField()
    doc_type = serializers.CharField()
    department = serializers.CharField()
    location = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    keywords = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    reason = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    jira = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    created_by = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    create_dt = serializers.DateTimeField()
    approved_dt = serializers.DateTimeField(required=False, default=None, allow_null=True)
    mod_ts = serializers.DateTimeField()
    comment = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    jira_create = serializers.BooleanField(required=False, default=False, allow_null=True)

class SpecSigSerializer(serializers.ModelSerializer):
    spec_one = serializers.BooleanField(source='role.spec_one')
    class Meta:
        model = SpecSig
        fields = ('role', 'signed_dt', 'from_am', 'spec_one', )

    def to_representation(self, value):
        data = super(SpecSigSerializer, self).to_representation(value)
        data['signer'] = value.signer.username if value.signer else None
        data['delegate'] = value.delegate.username if value.delegate else None
        return data

class SpecHistSerializer(serializers.ModelSerializer):
    upd_by = serializers.CharField(source='upd_by.username')
    class Meta:
        model = SpecHist
        fields = ('mod_ts', 'upd_by', 'change_type', 'comment', )

class SpecFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecFile
        fields = ('seq', 'filename', 'incl_pdf', 'file', )

class SpecReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecReference
        fields = ('num', 'ver', )

class SpecDetailSerializer(serializers.ModelSerializer):
    doc_type = serializers.StringRelatedField()
    department = serializers.StringRelatedField()
    created_by = serializers.StringRelatedField()
    class Meta:
        model = Spec
        fields = ('num', 'ver', 'title', 'doc_type', 'department', 'keywords', 'state', 'created_by',
            'create_dt', 'mod_ts', 'jira', 'anon_access', 'reason', 'approved_dt', 'sunset_extended_dt',
            'sunset_dt', 'sunset_warn_dt', 'location', )

    def to_representation(self, value):
        value.checkSunset()
        data = super(SpecDetailSerializer, self).to_representation(value)
        # Sort the related fields
        sigs = value.sigs.order_by('-from_am', 'role', ).all()
        data['sigs'] = SpecSigSerializer(sigs, many=True, context=self.context).data

        files = value.files.order_by('seq', ).all()
        data['files'] = SpecFileSerializer(files, many=True, context=self.context).data

        refs = value.refs.order_by('num', 'ver', ).all()
        data['refs'] = SpecReferenceSerializer(refs, many=True, context=self.context).data

        hist = value.hist.order_by('-mod_ts', '-id', ).all()
        data['hist'] = SpecHistSerializer(hist, many=True, context=self.context).data

        try:
            user = self.context.get("user")
            data['watched'] = user.watches.filter(num=value.num).first() != None
        except:  # AnonymousUser does not have the watches attribute
            data['watched'] = False

        if value.jira is not None and len(value.jira) > 0 \
            and settings.JIRA_URI is not None and len(settings.JIRA_URI) > 0:
            data['jira_url'] = f'{settings.JIRA_URI}/browse/{value.jira}'

        return data

class SpecListSerializer(serializers.ModelSerializer):
    doc_type = serializers.StringRelatedField()
    department = serializers.StringRelatedField()
    created_by = serializers.StringRelatedField()
    class Meta:
        model = Spec
        fields = ('num', 'ver', 'title', 'doc_type', 'department', 'keywords', 'state', 'created_by',
            'create_dt', 'mod_ts', 'jira', 'anon_access', 'reason', 'approved_dt', 'sunset_extended_dt',
            'sunset_dt', 'sunset_warn_dt', 'location', )

    def to_representation(self, value):
        value.checkSunset()
        data = super(SpecListSerializer, self).to_representation(value)

        # Property fields are not rendered the same as database fields. So updating the format here.
        if data["sunset_dt"]:
            data["sunset_dt"] = data["sunset_dt"].isoformat()
        if data["sunset_warn_dt"]:
            data["sunset_warn_dt"] = data["sunset_warn_dt"].isoformat()

        try:
            user = self.context.get("user")
            data['watched'] = user.watches.filter(num=value.num).first() != None
        except:  # AnonymousUser does not have the watches attribute
            data['watched'] = False

        return data

class SpecCreateSerializer(serializers.Serializer):
    num = serializers.IntegerField(required=False, default=None, allow_null=True)
    ver = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True, max_length=2)
    state = serializers.CharField()
    title = serializers.CharField()
    doc_type = serializers.CharField()
    department = serializers.CharField()
    keywords = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    location = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)

class SpecSigPutSerializer(serializers.Serializer):
    role = serializers.CharField()
    signer = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    from_am = serializers.BooleanField(required=False, default=False)

class SpecFilePutSerializer(serializers.Serializer):
    filename = serializers.CharField()
    incl_pdf = serializers.BooleanField(required=False, default=False)

class SpecPutSerializer(serializers.Serializer):
    num = serializers.IntegerField(required=False, default=None, allow_null=True)
    ver = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True, max_length=2)
    state = serializers.CharField()
    title = serializers.CharField()
    doc_type = serializers.CharField()
    department = serializers.CharField()
    keywords = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    location = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    jira = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    sigs = SpecSigPutSerializer(many=True)
    files = SpecFilePutSerializer(many=True)
    refs = SpecReferenceSerializer(many=True)
    anon_access = serializers.BooleanField(required=False, default=False, allow_null=True)
    reason = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    comment = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    created_by = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)

class FilePostSerializer(serializers.Serializer):
    file = serializers.FileField()

class SpecSignSerializer(serializers.Serializer):
    role = serializers.CharField()
    signer = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)

class SpecExtendSerializer(serializers.Serializer):
    comment = serializers.CharField()

class SpecRejectSerializer(serializers.Serializer):
    comment = serializers.CharField()

class SpecReviseSerializer(serializers.Serializer):
    reason = serializers.CharField()

