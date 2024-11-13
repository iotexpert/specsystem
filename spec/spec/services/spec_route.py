import os
import shutil
import subprocess
from pathlib import Path
from django.conf import settings
from django.core.files.base import File
from django.core.mail import EmailMessage
from rest_framework.exceptions import ValidationError
from PyPDF2 import PdfMerger
from spec.models import Spec, SpecFile, SpecHist, UserWatch
from subprocess import run
from utils.dev_utils import formatError
from . import jira

def genPdf(spec):
    # Skip generation if setup is not defined.
    if settings.SOFFICE is None:
        return # pragma nocover
    if shutil.which(settings.SOFFICE) is None: # pragma nocover
        raise ValidationError({"errorCode":"SPEC-R15", "error": f"LibreOffice application not found at: {settings.SOFFICE}"})

    pdfFileName=f"{spec.num}_{spec.ver}.pdf"
    # Remove any existing PDF file
    spec.files.filter(filename=pdfFileName).delete()

    tempFilePath = Path(settings.TEMP_PDF) / str(spec.num)
    tempPdfPath = tempFilePath / 'out'
    if tempFilePath.exists(): # pragma nocover
        shutil.rmtree(tempFilePath)
    try:
        os.makedirs(tempPdfPath)
        files = spec.files.filter(incl_pdf=True).all().order_by('seq')
        if len(files) == 0:
            return

        # Convert each file to pdf
        # Combine the file together
        with PdfMerger() as merger:
            for file in files:
                if os.path.splitext(file.file.path)[1] == '.pdf':
                    merger.append(file.file.path)
                else:
                    p = run([settings.SOFFICE, '--norestore', '--safe-mode', '--view', '--convert-to', 'pdf', '--outdir', str(tempPdfPath), file.file.path]
                        , stdout=subprocess.PIPE)
                    if p.returncode != 0: #pragma nocover
                        raise ValidationError({"errorCode":"SPEC-R10", "error": f"Error converting file ({file.file.path}) to PDF: {p.returncode} {p.stdout}"})
                    try:
                        fileName = os.path.splitext(tempPdfPath/file.file.name)[0]+'.pdf'
                        merger.append(fileName)
                    except BaseException as be: # pragma nocover
                        raise ValidationError({"errorCode":"SPEC-R13", "error": f"Error appending pdf file to merged pdf ({file.file.name}) to PDF: {be}"})
            try:
                merger.write(tempFilePath/pdfFileName)
            except BaseException as be: # pragma nocover
                raise ValidationError({"errorCode":"SPEC-R19", "error": f"Error creating merged pdf file: {be}"})

        # Save file to spec
        specFile = SpecFile.objects.create(spec=spec, seq=0, filename=pdfFileName, incl_pdf=False)
        with open(tempFilePath/pdfFileName, mode='rb') as f:
            specFile.file.save(pdfFileName, File(f))
    except BaseException as be: # pragma nocover
        formatError(be, "SPEC-R14")

    finally:
        # Clean up the folder, no matter success or failure
        try:
            if tempFilePath.exists():
                shutil.rmtree(tempFilePath)
        except BaseException as be: # pragma nocover
            pass

def specSubmit(request, spec):
    try:
        if spec.state != 'Draft':
            raise ValidationError({"errorCode":"SPEC-R01", "error": "Spec must be in Draft state to submit for signatures"})
        if spec.files.all().count() == 0:
            raise ValidationError({"errorCode":"SPEC-R02", "error": "Spec must be have at least one attached file."})
        if spec.sigs.all().count() == 0:
            raise ValidationError({"errorCode":"SPEC-R03", "error": "Spec must be have at least one signature."})
        missingSigs = list(spec.sigs.filter(role__spec_one=True, signer__isnull=True).values_list('role', flat=True))
        if len(missingSigs) > 0:
            raise ValidationError({"errorCode":"SPEC-R04", "error": f"Signer must be specified for Role(s): {', '.join(missingSigs)}"})

        spec.mod_ts = request._req_dt
        spec.state = 'Signoff'
        spec.save()

        # Clear any signatures that may have been inadvertantly left
        for sig in spec.sigs.all():
            sig.delegate = None
            sig.signed_dt = None
            sig.save()

        SpecHist.objects.create(
            spec=spec,
            mod_ts = request._req_dt,
            upd_by = request.user,
            change_type = 'Submit',
            comment = ''
        )

        genPdf(spec)
        jira.submit(spec)

        to = spec.sigs.filter(signer__isnull=False,signer__email__isnull=False).values_list('signer__email', flat=True)
        if len(to) > 0 and settings.EMAIL_HOST is not None and len(settings.EMAIL_HOST) > 0:
            email = EmailMessage(
                subject=f'{"[From Test]" if os.environ["AD_SUFFIX"] == "Test" else ""} Spec {spec.num} "{spec.title}" needs your review',
                body=f'''{"[From Test]" if os.environ["AD_SUFFIX"] == "Test" else ""} Spec {spec.num}/{spec.ver} "{spec.title}" needs your review
                {request.build_absolute_uri('/ui-spec/'+str(spec.num)+'/'+spec.ver)}
                ''',
                from_email=settings.EMAIL_HOST_USER,
                to=to,
                reply_to=[spec.created_by.email],
            )
            email.send(fail_silently=False)

        return spec
    except BaseException as be: # pragma nocover
        formatError(be, "SPEC-R17")

def specSign(request, spec, validated_data):
    try:
        if spec.state != 'Signoff':
            raise ValidationError({"errorCode":"SPEC-R06", "error": "Spec must be in Signoff state to accept signatures"})

        sig = spec.sigs.filter(role__role=validated_data['role'], signer__username=validated_data['signer']).first()
        if sig is None:
            raise ValidationError({"errorCode":"SPEC-R11", "error": f"Spec does not have Role {validated_data['role']} / Signer {validated_data['signer']} entry."})
        if sig.delegate is not None:
            return spec # Already signed

        if not request.user.is_superuser:
            # if a specific signer isn't specified, they must be in the users for the role, if any
            if sig.signer is None:
                if sig.role.users.count() > 0 and not sig.role.isMember(request.user):
                    raise ValidationError({"errorCode":"SPEC-R16", "error": f"Current user {request.user.username} is not valid for role. Options are: {list(sig.role.users.values('user__username').values_list('user__username', flat=True))}"})
            # If user is not the designated signer, see if they are an admin or delegate
            elif request.user != sig.signer:
                if request.user.username not in sig.signer.delegates.values_list('delegate__username', flat=True):
                    raise ValidationError({"errorCode":"SPEC-R12", "error": f"Current user {request.user.username} is not a delegate for {sig.signer.username}"})
        sig.delegate = request.user
        sig.signed_dt = request._req_dt
        sig.save()
        SpecHist.objects.create(
            spec=spec,
            mod_ts = request._req_dt,
            upd_by = request.user,
            change_type = 'Sign',
            comment = f'Signature of Role: {sig.role.role}, Signer: {(sig.signer or None) and sig.signer.username}, Performed by: {request.user.username}'
        )

        # If not completely signed, return the current spec
        toBeSigned = spec.sigs.filter(delegate__isnull=True).count()
        if toBeSigned > 0:
            return spec

        # Signatures complete, so Obsolete any previous version and activate this one.
        specs = Spec.objects.filter(num=spec.num, state='Active')
        for s in specs:
            s.mod_ts = request._req_dt
            s.state = 'Obsolete'
            s.save()

            SpecHist.objects.create(
                spec=s,
                mod_ts = request._req_dt,
                upd_by = request.user,
                change_type = 'Obsolete',
                comment = f'Obsoleted by release of {spec.num}/{spec.ver}'
            )

        spec.mod_ts = request._req_dt
        spec.approved_dt = request._req_dt
        spec.state = 'Active'
        spec.save()

        SpecHist.objects.create(
            spec=spec,
            mod_ts = request._req_dt,
            upd_by = request.user,
            change_type = 'Activate',
            comment = f''
        )

        jira.active(spec)

        to = UserWatch.objects.filter(num=spec.num, user__email__isnull=False).values_list('user__email', flat=True)
        if len(to) > 0 and settings.EMAIL_HOST is not None and len(settings.EMAIL_HOST) > 0:
            email = EmailMessage(
                subject=f'{"[From Test]" if os.environ["AD_SUFFIX"] == "Test" else ""} A new version of Spec {spec.num} "{spec.title}" you are watching has been activated.',
                body=f'''{"[From Test]" if os.environ["AD_SUFFIX"] == "Test" else ""} A new version of Spec {spec.num} "{spec.title}" you are watching has been activated.
                {request.build_absolute_uri('/ui-spec/'+str(spec.num)+'/'+spec.ver)}
                ''',
                from_email=settings.EMAIL_HOST_USER,
                to=to,
                reply_to=[spec.created_by.email],
            )
            email.send(fail_silently=False)

        return spec
    except BaseException as be: # pragma nocover
        formatError(be, "SPEC-R18")

def specReject(request, spec, validated_data):
    if spec.state != 'Signoff':
        raise ValidationError({"errorCode":"SPEC-R07", "error": "Spec must be in Signoff state to reject"})

    spec.mod_ts = request._req_dt
    spec.state = 'Draft'
    spec.save()

    # Clear any signatures
    for sig in spec.sigs.all():
        sig.delegate = None
        sig.signed_dt = None
        sig.save()

    # Remove the generated .pdf file
    SpecFile.objects.filter(spec=spec, filename=f"{spec.num}_{spec.ver}.pdf").delete()

    SpecHist.objects.create(
        spec=spec,
        mod_ts = request._req_dt,
        upd_by = request.user,
        change_type = 'Reject',
        comment = validated_data['comment']
    )

    jira.reject(spec)

    if settings.EMAIL_HOST is not None and len(settings.EMAIL_HOST) > 0:
        email = EmailMessage(
            subject=f'{"[From Test]" if os.environ["AD_SUFFIX"] == "Test" else ""} Spec {spec.num}/{spec.ver} "{spec.title}" has been rejected by {request.user.username}',
            body=f'''{"[From Test]" if os.environ["AD_SUFFIX"] == "Test" else ""} Spec {spec.num}/{spec.ver} "{spec.title}" has been rejected by {request.user.username}
            {request.build_absolute_uri('/ui-spec/'+str(spec.num)+'/'+spec.ver)}
            Reason: {validated_data['comment']}
            ''',
            from_email=settings.EMAIL_HOST_USER,
            to=[spec.created_by.email, ],
            reply_to=[request.user.email],
        )
        email.send(fail_silently=False)

    return spec

def specExtend(request, spec, validated_data):
    if spec.state != 'Active':
        raise ValidationError({"errorCode":"SPEC-R08", "error": "Spec must be in Active state to extend sunset period"})
    if spec.sunset_extended_dt is not None:
        raise ValidationError({"errorCode":"SPEC-R09", "error": "Spec sunset date can only be extended once. Create a new revision."})

    spec.mod_ts = request._req_dt
    spec.sunset_extended_dt = request._req_dt
    spec.save()

    SpecHist.objects.create(
        spec=spec,
        mod_ts = request._req_dt,
        upd_by = request.user,
        change_type = 'Extend',
        comment = validated_data['comment']
    )

    return spec

