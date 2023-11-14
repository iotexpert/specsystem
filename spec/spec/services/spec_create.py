import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from rest_framework.exceptions import ValidationError
from spec.services.revletter import get_next_version, valid_rev
from user.models import User
from ..models import ApprovalMatrix, Department, DocType, Location, Role, Spec, SpecHist, SpecSig, SpecFile, SpecReference, UserWatch
from . import jira


def specImport(request, validated_data):
    """Used for initial import of specs to specified state with specified dates"""
    comment = validated_data.pop("comment")
    jira_create = validated_data.pop("jira_create")

    if not valid_rev(validated_data['ver']):
        raise ValidationError({"errorCode":"SPEC-C06", "error": f"Ver can only contain uppercase letters."})

    validated_data['doc_type'] = DocType.lookupOrCreate(validated_data['doc_type'])
    validated_data['department'] = Department.lookupOrCreate(validated_data['department'])
    validated_data['location'] = Location.lookupOrCreate(validated_data['location'])

    # If we can find the created_by user specified, use it
    # Otherwise, user the user doing the load
    try:
        validated_data['created_by'] = User.lookup(validated_data['created_by'])
    except:
        validated_data['created_by'] = request.user

    spec = Spec.objects.filter(num = validated_data['num'], ver = validated_data['ver']).first()
    if spec:
        spec.state = validated_data['state']
        spec.title = validated_data['title']
        spec.doc_type = validated_data['doc_type']
        spec.department = validated_data['department']
        spec.location = validated_data['location']
        spec.state = validated_data['state']
        spec.keywords = validated_data['keywords']
        spec.reason = validated_data['reason']
        spec.jira = validated_data['jira']
        spec.created_by = validated_data['created_by']
        spec.create_dt = validated_data['create_dt']
        spec.approved_dt = validated_data['approved_dt']
        spec.mod_ts = validated_data['mod_ts']
        spec.save()
    else:
        spec = Spec.objects.create(**validated_data)

    if not comment:
        comment = 'Initial Load'
    SpecHist.objects.create(
        spec=spec,
        mod_ts = request._req_dt,
        upd_by = request.user,
        change_type = 'Import',
        comment = comment
    )

    if jira_create:
        jira.create(spec)
        jira.submit(spec)
        jira.active(spec)

    return spec

def specSigCreate(request, spec, role, signerName, from_am):
    if signerName:
        signer = User.lookup(username=signerName)
    else:
        signer = None

    # If the role has users specified, the signer must be in the list
    if signer and role.users.count() > 0 and not role.isMember(signer):
        raise ValidationError({"errorCode":"SPEC-C07",
            "error": f"Signer {signer} for Role {role.role} needs to be in list: {list(role.users.values('user__username').values_list('user__username', flat=True))}"})

    if not from_am and signer:
        specRole = SpecSig.objects.filter(spec=spec, role=role, signer=None, from_am=True).first()
        if specRole:
            specRole.signer = signer
            specRole.save()
            return

    specRole = SpecSig.objects.create(spec=spec, role=role, signer=signer, from_am=from_am)

def specSetReqSigs(request, spec):
    spec.sigs.all().delete()
    signRoles = ApprovalMatrix.lookupRoles(spec.doc_type, spec.department)
    for signRole in signRoles:
        specSigCreate(request, spec, signRole.role, None, True)

def specCreate(request, validated_data):
    docTypeName = validated_data.pop("doc_type")
    deptName = validated_data.pop("department")
    location = validated_data.pop("location")

    validated_data['doc_type'] = DocType.lookup(docTypeName)
    validated_data['department'] = Department.lookup(deptName)
    validated_data['location'] = Location.lookup(location)

    if validated_data['num'] is not None:
        if not request.user.is_superuser:
            raise ValidationError({"errorCode":"SPEC-C02", "error": f"Only Admins can create a spec with a specific number"})
        if not validated_data['ver'] or len(validated_data['ver']) == 0:
            raise ValidationError({"errorCode":"SPEC-C03", "error": f"Ver must be specified, when Num is specified"})
        if not valid_rev(validated_data['ver']):
            raise ValidationError({"errorCode":"SPEC-C05", "error": f"Ver can only contain uppercase letters."})

        specNum = Spec.objects.filter(num=validated_data['num']).first()
        if specNum:
            raise ValidationError({"errorCode":"SPEC-C04", "error": f"Num {validated_data['num']} is already used in the system."})

        validated_data['ver'] = validated_data['ver'].upper()
    else:
        specNum = Spec.objects.values('num').order_by('-num').values_list('num', flat=True).first()
        validated_data['num'] = specNum + 1 if specNum else 1
        validated_data['ver'] = 'A'

    validated_data['state'] = 'Draft'
    validated_data['created_by'] = request.user
    validated_data['create_dt'] = request._req_dt
    validated_data['mod_ts'] = request._req_dt
    validated_data['reason'] = 'Initial Version'

    spec = Spec.objects.create(**validated_data)

    specSetReqSigs(request, spec)

    jira.create(spec)

    return spec

def specRevise(request, spec, validated_data):
    # Grab a copy of the spec being copied for related items below.
    orig_spec = Spec.objects.get(id=spec.id)

    inProcessSpec = Spec.objects.filter(num=spec.num, state__in=['Draft', 'Signoff']).first()
    if inProcessSpec is not None:
        raise ValidationError({"errorCode":"SPEC-C01", "error": f"Version {inProcessSpec.ver} is in state {inProcessSpec.state}. Cannot start a new revision."})

    # Get the latest revision, incase they are copying an obsolete version instead of the active version
    latestSpec = Spec.objects.filter(num=spec.num).order_by('-ver').first()

    spec.id = None
    spec.ver = get_next_version(latestSpec.ver)
    spec.state = 'Draft'
    spec.created_by = request.user
    spec.create_dt = request._req_dt
    spec.mod_ts = request._req_dt
    spec.jira = None
    spec.reason = validated_data['reason']
    spec.approved_dt = None
    spec.sunset_extended_dt = None

    spec.save()

    specSetReqSigs(request, spec)

    for ref_data in orig_spec.refs.all():
        ref_data.id = None
        ref_data.spec=spec
        ref_data.save()

    jira.create(spec)

    to = UserWatch.objects.filter(num=spec.num, user__email__isnull=False).values_list('user__email', flat=True)
    if len(to) > 0 and settings.EMAIL_HOST is not None and len(settings.EMAIL_HOST) > 0:
        email = EmailMessage(
            subject=f'{"[From Test]" if os.environ["AD_SUFFIX"] == "Test" else ""} Spec {spec.num} "{spec.title}" you are watching is being revised by {spec.created_by.username}',
            body=f'''{"[From Test]" if os.environ["AD_SUFFIX"] == "Test" else ""} Spec {spec.num} "{spec.title}" you are watching is being revised by {spec.created_by.username}
            {request.build_absolute_uri('/ui-spec/'+str(spec.num)+'/'+spec.ver)}

            Reason for change:
            {spec.reason}
            ''',
            from_email=settings.EMAIL_HOST_USER,
            to=to,
            reply_to=[spec.created_by.email],
        )
        email.send(fail_silently=False)

    return spec