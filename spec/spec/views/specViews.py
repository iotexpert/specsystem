import csv
import io
import json
import os
import subprocess
from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import render
from pathlib import Path
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import status
from rest_framework.decorators import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from subprocess import run

from proj.util import IsSuperUser
from spec.views.view_queries.spec_list import SpecListSerializer, getSpecListQuerySet
from utils.raw_sql import RawSQLPagination
from ..services import jira
from ..services.spec_route import specExtend, specReject, specSign, specSubmit
from ..services.spec_create import specCreate, specImport, specRevise
from ..services.spec_update import specFileUpload, specUpdate
from utils.dev_utils import formatError

from ..models import Spec, SpecFile, SpecHist
from ..serializers.specSerializers import FilePostSerializer, ImportSpecSerializer, SpecCreateSerializer, SpecExtendSerializer, SpecPutSerializer, SpecRejectSerializer, SpecReviseSerializer, SpecDetailSerializer, SpecSignSerializer


def genCsv(request, outFileName, serializer, queryset):
    """
    Generate a CSV file with the data from the array of dictionary entries
    Return the file as output.
    """
    try:
        f = io.StringIO()
        w = None
        for r in queryset:
            d = serializer.to_representation(r)
            if not w:
                w = csv.DictWriter(f, d.keys())
                w.writeheader()
            w.writerow(d)

        f.seek(0)
        response = FileResponse(io.BytesIO(f.read().encode('utf8')), filename=outFileName)
        return response
    except BaseException as be: # pragma nocover
        formatError(be, "SPEC-SV28")

class HelpFile(APIView):
    """
    get:
    help/<doc>
    Return specific file (user, admin, design)
    """
    def genPdf(self, doc):
        if doc.lower() == 'user':
            osFileName = 'help/user_guide.docx'
            filename = 'user_guide.pdf'
        elif doc.lower() == 'admin':
            osFileName = 'help/admin_guide.docx'
            filename = 'admin_guide.pdf'
        elif doc.lower() == 'design':
            osFileName = 'help/high_level_design.docx'
            filename = 'high_level_design.pdf'
        else:
            raise ValidationError({
                "errorCode": "SPEC-SV26", "error":
                f"Valid help choices are: 'user' for the User Guide, 'admin' for the Admin Guide and 'design' for the High Level Design"})


        osPdfFileName = os.path.splitext(osFileName)[0]+'.pdf'
        if not Path(osPdfFileName).exists(): # pragma nocover
            p = run([settings.SOFFICE, '--norestore', '--safe-mode', '--view', '--convert-to', 'pdf', '--outdir', str(Path(osFileName).parent), osFileName]
                , stdout=subprocess.PIPE)
            if p.returncode != 0:
                raise ValidationError({"errorCode":"SPEC-SV27", "error": f"Error converting file ({osFileName}) to PDF: {p.returncode} {p.stdout}"})
        return (osPdfFileName, filename)

    def get(self, request, doc, format=None):
        try:
            (osFileName, filename) = self.genPdf(doc.lower())
            response = FileResponse(open(osFileName, 'rb'), filename=filename)
            return response
        except BaseException as be: # pragma: no cover
            try:
                formatError(be, "SPEC-SV25")
            except ValidationError as exc:
                return render(request, 'file_error_page.html', exc.detail, status=400)

class ImportSpec(GenericAPIView):
    """
    post:
    Used for initial import of specs to specified state with specified dates

    {
        "num": {{id}},
        "ver": "{{Revision}}",
        "state": "{{State}}",
        "title": "{{Document Name}}",
        "keywords": "",
        "location": "{{Location}}",
        "doc_type": "{{Document Type}}",
        "department": "{{Department}}",
        "reason": "{{Document Subject}}",
        "created_by": "{{Created By}}",
        "create_dt": "{{Creation Date}}",
        "mod_ts": "{{Modification Date}}",
        "approved_dt": "{{Date Released}}",
        "comment": "Owner: {{Owner}}\nDescription: {{Description}}\nReferences: {{Refereneces}}",
        "jira_create": false
    }
    """
    permission_classes = [IsSuperUser]
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = ImportSpecSerializer(data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-SV23", "error": "Invalid message format", "schemaErrors":serializer.errors})
                spec = specImport(request, serializer.validated_data)
            serializer = SpecDetailSerializer(spec, context={'user':request.user})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV24")

class SpecList(GenericAPIView):
    """
    get:
    spec/
    spec/<num>
    Return list of specs

    post:
    Create spec

    {
        "title": "REQ, SPEC SYSTEM",
        "doc_type": "Requirement",
        "department": "IT",
        "keywords": "SPEC",
        "location": "Corporate",
        "sigs": [{"role": "ITMgr", "signer": "ahawse"}],
        "files": [{"filename": "Req.docx", "seq": 1}],
        "refs": [{"num": 300000, "ver": "A"}]
    }
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request, num=None, format=None):
        try:
            reqDict = request.GET.copy()
            if num:
                reqDict['num'] = num

            if 'state' in reqDict:
                reqDict['state'] = request.GET.get('state').split(",")

            if not request.GET.get('incl_obsolete'):
                reqDict['not_incl_obsolete'] = '^Obsolete$'

            queryset = getSpecListQuerySet(reqDict)
            # If requested, return the entire data set in a csv file
            if request.GET.get('output_csv'):
                ret_data = queryset.get_all_data()
                # Watch is a UI focused value.
                for dicts in ret_data:
                    dicts["watched"] = False
                return genCsv(request, 'spec_list.csv', SpecListSerializer(), ret_data)

            pagination = RawSQLPagination()
            page = pagination.paginate_queryset(queryset, request)
            # Need to set a value based on the user making a request.
            for row in page:
                watched = False
                if request.user and row["watched"]:
                    watched_arr = json.loads(row['watched']) if row['watched'] else []
                    for w in watched_arr:
                        if request.user.username == w["username"]:
                            watched = True
                row["watched"] = watched
            serializer = SpecListSerializer(page, many=True)
            return pagination.get_paginated_response(serializer.data)

        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV01")

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = SpecCreateSerializer(data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-SV02", "error": "Invalid message format", "schemaErrors":serializer.errors})
                spec = specCreate(request, serializer.validated_data)
            serializer = SpecDetailSerializer(spec, context={'user':request.user})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV03")


class SpecDetail(APIView):
    """
    get:
    spec/<num>/<ver>
    Return details of specific Spec

    put:
    spec/<num>/<ver>
    Update spec

    {
        "state": "Draft",
        "title": "REQ, SPEC SYSTEM",
        "keywords": "SPEC",
        "cat": "IT",
        "sub_cat": "Requirement",
        "sigs": [{"role": "ITMgr", "signer": "ahawse"}],
        "files": [{"filename": "Req.docx", "seq": 1}],
        "refs": [{"num": 300000, "ver": "A"}],
        "reason": "Spec being changed for this reason",
        "comment": "Changes made today"
    }

    post:
    spec/<num>/<ver>
    Create a new revision of the spec

    {
        "reason": "Spec being revised for this reason"
    }

    delete:
    spec/<num>/<ver>
    Delete specified spec entry
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, num, ver, format=None):
        try:
            spec = Spec.lookup(int(num), ver, request.user)
            serializer = SpecDetailSerializer(spec, context={'user':request.user})
            return Response(serializer.data)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV04")

    def put(self, request, num, ver, format=None):
        try:
            with transaction.atomic():
                spec = Spec.lookup(num, ver, request.user)
                serializer = SpecPutSerializer(spec, data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-SV05", "error": "Invalid message format", "schemaErrors":serializer.errors})
                spec = specUpdate(request, spec, serializer.validated_data)
            serializer = SpecDetailSerializer(spec, context={'user':request.user})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV06")

    def post(self, request, num, ver, format=None):
        try:
            with transaction.atomic():
                spec = Spec.lookup(num, ver, request.user)
                serializer = SpecReviseSerializer(spec, data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-SV07", "error": "Invalid message format", "schemaErrors":serializer.errors})
                spec = specRevise(request, spec, serializer.validated_data)
            serializer = SpecDetailSerializer(spec, context={'user':request.user})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV08")

    def delete(self, request, num, ver, format=None):
        try:
            with transaction.atomic():
                spec = Spec.lookup(num, ver, request.user)
                if spec.state != 'Draft':
                    raise ValidationError({"errorCode":"SPEC-SV22", "error": "Spec is not in Draft state. Cannot delete."})
                jira.delete(spec)
                spec.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV09")


class SpecFileDetail(APIView):
    """
    get:
    file/<num>/<?ver>/<?fileName>
    Return details of specific file

    post:
    file/<num>/<ver>
    Uploads a file to spec

    {
        "file": {
            "name":"Inv.docx",
            "file":<_io.BytesIO object>
        }
    }

    delete:
    file/<num>/<ver>/<fileName>
    Delete file from spec
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, num, ver="*", fileName=None, format=None):
        try:
            specFile = SpecFile.lookup(num, ver, fileName, request)
            osFileName = specFile.file.path
            response = FileResponse(open(osFileName, 'rb'), filename=specFile.filename)
            return response
        except BaseException as be: # pragma: no cover
            try:
                formatError(be, "SPEC-SV10")
            except ValidationError as exc:
                return render(request, 'file_error_page.html', exc.detail, status=400)

    def post(self, request, num, ver, format=None):
        try:
            with transaction.atomic():
                spec = Spec.lookup(num, ver, request.user)
                spec.checkEditable(request.user)
                serializer = FilePostSerializer(spec, data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-SV11", "error": "Invalid message format", "schemaErrors":serializer.errors})
                spec = specFileUpload(request, spec, serializer.validated_data)
                if spec.state != 'Draft':
                    SpecHist.objects.create(
                        spec=spec,
                        mod_ts = request._req_dt,
                        upd_by = request.user,
                        change_type = 'Admin Update',
                        comment = f'File {serializer.validated_data["file"].name} added while spec in state: {spec.state}'
                    )
            serializer = SpecDetailSerializer(spec, context={'user':request.user})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV12")

    def delete(self, request, num, ver, fileName, format=None):
        try:
            with transaction.atomic():
                spec = Spec.lookup(num, ver, request.user)
                spec.checkEditable(request.user)
                SpecFile.objects.filter(spec=spec, filename=fileName).delete()
                if spec.state != 'Draft':
                    SpecHist.objects.create(
                        spec=spec,
                        mod_ts = request._req_dt,
                        upd_by = request.user,
                        change_type = 'Admin Update',
                        comment = f'File {fileName} deleted while spec in state: {spec.state}'
                    )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV13")


class SpecSubmit(APIView):
    """
    post:
    submit/<num>/<ver>
    Submit spec for signatures

    {
    }
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    def post(self, request, num, ver, format=None):
        try:
            with transaction.atomic():
                spec = Spec.lookup(num, ver, request.user)
                spec = specSubmit(request, spec)
            serializer = SpecDetailSerializer(spec, context={'user':request.user})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV14")


class SpecSign(APIView):
    """
    post:
    sign/<num>/<ver>
    Sign spec

    {
        "role":"ITMgr",
        "signer":"ahawse"
    }
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    def post(self, request, num, ver, format=None):
        try:
            with transaction.atomic():
                spec = Spec.lookup(num, ver, request.user)
                serializer = SpecSignSerializer(data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-SV15", "error": "Invalid message format", "schemaErrors":serializer.errors})
                spec = specSign(request, spec, serializer.validated_data)
            serializer = SpecDetailSerializer(spec, context={'user':request.user})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV16")



class SpecReject(APIView):
    """
    post:
    reject/<num>/<ver>
    Reject spec send back to Draft

    {
    }
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    def post(self, request, num, ver, format=None):
        try:
            with transaction.atomic():
                spec = Spec.lookup(num, ver, request.user)
                serializer = SpecRejectSerializer(data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-SV17", "error": "Invalid message format", "schemaErrors":serializer.errors})
                spec = specReject(request, spec, serializer.validated_data)
            serializer = SpecDetailSerializer(spec, context={'user':request.user})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV18")



class SpecExtend(APIView):
    """
    post:
    extend/<num>/<ver>
    Extend spec sunset date

    {
        "comment": "No changes required. Still in use."
    }
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    def post(self, request, num, ver, format=None):
        try:
            with transaction.atomic():
                spec = Spec.lookup(num, ver, request.user)
                serializer = SpecExtendSerializer(data=request.data)
                if not serializer.is_valid():
                    raise ValidationError({"errorCode":"SPEC-SV19", "error": "Invalid message format", "schemaErrors":serializer.errors})
                spec = specExtend(request, spec, serializer.validated_data)
            serializer = SpecDetailSerializer(spec, context={'user':request.user})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV20")

class SunsetList(APIView):
    """
    get:
    sunset/
    Return list of specs approaching sunset date (doc_type has sunset defined and spec is past the warn threshold)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request, num=None, format=None):
        try:
            reqDict = {'past_warn_date': '^Active$'}

            queryset = getSpecListQuerySet(reqDict)
            # If requested, return the entire data set in a csv file
            if request.GET.get('output_csv'):
                ret_data = queryset.get_all_data()
                # Watch is a UI focused value.
                for dicts in ret_data:
                    dicts["watched"] = False
                return genCsv(request, 'sunset_list.csv', SpecListSerializer(), ret_data)

            pagination = RawSQLPagination()
            page = pagination.paginate_queryset(queryset, request)
            # Watch is a UI focused value.
            for dicts in page:
                dicts["watched"] = False
            serializer = SpecListSerializer(page, many=True)
            return pagination.get_paginated_response(serializer.data)

        except BaseException as be: # pragma: no cover
            formatError(be, "SPEC-SV21")
