from rest_framework.exceptions import ValidationError
from .spec_create import specSetReqSigs, specSigCreate
from ..models import Department, DocType, Location, Role, SpecFile, SpecHist, SpecReference
from user.models import User

def specUpdate(request, spec, validated_data):
    spec.checkEditable(request.user)

    if spec.state != validated_data['state']:
        if not request.user.is_superuser:
            raise ValidationError({"errorCode":"SPEC-U52", "error": "State changes via update can only be done by an administrator."})
        if not validated_data['comment'] or len(validated_data['comment']) == 0:
            raise ValidationError({"errorCode":"SPEC-U53", "error": "State changes updates require a comment."})
        spec.state = validated_data['state']

        if spec.state == 'Active' and spec.approved_dt is None:
            spec.approved_dt = request._req_dt

    if validated_data['created_by'] and spec.created_by.username != validated_data['created_by']:
        created_by = User.lookup(username=validated_data['created_by'])
        if not request.user.is_superuser:
            raise ValidationError({"errorCode":"SPEC-U54", "error": "Created By changes via update can only be done by an administrator."})
        SpecHist.objects.create(
            spec=spec,
            mod_ts = request._req_dt,
            upd_by = request.user,
            change_type = 'Admin Update',
            comment = f'Created By changed from {spec.created_by.username} to {created_by.username}'
        )
        spec.created_by = created_by

    # Only superusers can set the anon_access.
    if request.user.is_superuser:
        spec.anon_access = validated_data['anon_access']

    spec.mod_ts = request._req_dt

    sigs_data = validated_data.pop("sigs")
    refs_data = validated_data.pop("refs")
    files_data = validated_data.pop("files")

    spec.doc_type = DocType.lookup(validated_data.pop("doc_type"))
    spec.department = Department.lookup(validated_data.pop("department"))
    spec.location = Location.lookup(validated_data.pop("location"))
    spec.title = validated_data.pop("title")
    spec.keywords = validated_data.pop("keywords")
    spec.jira = validated_data.pop("jira")
    spec.reason = validated_data.pop("reason")
    spec.save()

    # If spec is not in draft state, don't touch the signatures for an admin edit.
    if spec.state == 'Draft':
        # Clear previous sig entries, preload required sigs
        specSetReqSigs(request, spec)
        for sig_data in sigs_data:
            if sig_data['from_am'] and not sig_data['signer']:
                continue
            specSigCreate(request, spec, Role.lookup(sig_data['role']), sig_data['signer'], False)

    # Clear the previous references
    spec.refs.all().delete()
    for ref_data in refs_data:
        ref_data['spec'] = spec
        SpecReference.objects.create(**ref_data)

    # For files, this update will only update the attributes
    seq = 0
    for file_data in files_data:
        seq += 1
        spec.files.filter(filename=file_data['filename']).update(seq=seq)
        spec.files.filter(filename=file_data['filename']).update(incl_pdf=file_data['incl_pdf'])

    if spec.state != 'Draft':
        SpecHist.objects.create(
            spec=spec,
            mod_ts = request._req_dt,
            upd_by = request.user,
            change_type = 'Admin Update',
            comment = f'Admin update made while spec in state: {spec.state}'
        )
    if validated_data['comment'] and len(validated_data['comment']) > 0:
        SpecHist.objects.create(
            spec=spec,
            mod_ts = request._req_dt,
            upd_by = request.user,
            change_type = 'Update',
            comment = validated_data['comment']
        )

    return spec


def specFileUpload(request, spec, validated_data):
    validated_data['spec'] = spec
    validated_data['seq'] = spec.files.count()+1
    validated_data['filename'] = validated_data['file'].name
    validated_data['incl_pdf'] = False

    specFile = SpecFile.objects.create(**validated_data)

    return spec