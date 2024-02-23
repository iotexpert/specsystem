import re
from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from django.db import models
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from user.models import User as SpecUser

class UserDelegate(models.Model):
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE, related_name='delegates')
    delegate = models.ForeignKey(DjangoUser, on_delete=models.CASCADE, related_name='delegates_for')

    class Meta:
        managed = True
        db_table = 'user_delegate'

class UserWatch(models.Model):
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE, related_name='watches')
    num = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'user_watch'

class DocType(models.Model):
    name = models.CharField(primary_key=True, max_length=50)
    descr = models.CharField(max_length=4000, blank=True, null=True)
    confidential = models.BooleanField(default=False, blank=True)
    jira_temp = models.CharField(max_length=4000, blank=True, null=True)
    sunset_interval = models.DurationField(blank=True, null=True)
    sunset_warn = models.DurationField(blank=True, null=True)
    active = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = True
        db_table = 'doc_type'

    def __str__(self):
        return self.name

    @staticmethod
    def lookup(docTypeName):
        doctype = DocType.objects.filter(name=docTypeName).first()
        if not doctype:
            raise ValidationError({"errorCode":"SPEC-M01", "error": f"Document Type: {docTypeName} does not exist."})
        return doctype

    @staticmethod
    def lookupOrCreate(docTypeName):
        docTypeName=re.sub(r'[^-a-zA-Z0-9_:]','_',docTypeName) # translate illegal characters to an _
        doctype = DocType.objects.filter(name=docTypeName).first()
        if doctype:
            return doctype
        return DocType.objects.create(name=docTypeName)

class Role(models.Model):
    role = models.CharField(primary_key=True, max_length=50)
    descr = models.CharField(max_length=4000, blank=True, null=True)
    spec_one = models.BooleanField(default=True, blank=True)
    active = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = True
        db_table = 'role'

    @staticmethod
    def lookup(roleName):
        role = Role.objects.filter(role=roleName).first()
        if not role:
            raise ValidationError({"errorCode":"SPEC-M02", "error": f"Role: {roleName} does not exist."})
        return role

    def isMember(self, user):
        for roleUser in self.users.all():
            if user == roleUser.user:
                return True
        return False

class RoleUser(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE, related_name='+')
    descr = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'role_user'

    def __str__(self):
        if self.descr is not None and len(self.descr) > 0:
            return self.user.username + ':' + self.descr
        return self.user.username

class Department(models.Model):
    name = models.CharField(primary_key=True, max_length=150)
    active = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = True
        db_table = 'department'

    def __str__(self):
        return self.name

    @staticmethod
    def lookup(deptName):
        dept = Department.objects.filter(name=deptName).first()
        if not dept:
            raise ValidationError({"errorCode":"SPEC-M03", "error": f"Department: {deptName} does not exist."})
        return dept

    @staticmethod
    def lookupOrCreate(deptName):
        deptName=re.sub(r'[^-a-zA-Z0-9_:]','_',deptName) # translate illegal characters to an _
        deptName=re.sub(r':{2,}',':',deptName) # Remove consecutive colons (blank department path item)
        deptName=re.sub(r':$','',deptName) # Remove trailing colon (blank department path)
        doctype = Department.objects.filter(name=deptName).first()
        if doctype:
            return doctype
        return Department.objects.create(name=deptName)

    def parents(self):
        """return list of this department and all its parents"""
        deptList = [self]

        deptName = self.name
        while ':' in deptName:
            # Remove the last : and everything after it, to check on the department's parent
            deptName = re.sub(':[^:]*$', '', deptName)

            try: # Department not existing is just not added to the array
                department = Department.lookup(deptName)
                deptList.append(department)
            except: # pragma nocover
                pass

        try: # Department __Generic__ not existing is just not added to the array
            department = Department.lookup('__Generic__')
            deptList.append(department)
        except: # pragma nocover
            pass

        return deptList

    def isReader(self, user):
        for dept in self.parents():
            for role in dept.readRoles.all():
                if role.role.isMember(user):
                    return True
        return False

class DepartmentReadRole(models.Model):
    dept = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='readRoles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'dept_read_role'

    def __str__(self):
        return self.role.role

class ApprovalMatrix(models.Model):
    doc_type = models.ForeignKey(DocType, on_delete=models.CASCADE, related_name='+')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='+', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'apvl_mt'
        unique_together = (('doc_type', 'department'),)

    @staticmethod
    def lookupRoles(doc_type, origDept, orig_dept=None):
        """
        Find all the Roles required.
        Match on doc_type and department. Then remove the tail of the department after the colon and check again.
        The combined list of roles from the specific department upto the __Generic__ department are added into the list.
        """
        ret = []

        for dept in origDept.parents():
            apvl_mt = ApprovalMatrix.objects.filter(doc_type=doc_type, department=dept).first()
            if apvl_mt:
                ret = ret + list(apvl_mt.signRoles.all())

        return ret

class ApprovalMatrixSignRole(models.Model):
    apvl_mt = models.ForeignKey(ApprovalMatrix, on_delete=models.CASCADE, related_name='signRoles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'apvl_mt_sign_role'

    def __str__(self):
        return self.role.role

class Location(models.Model):
    name = models.CharField(primary_key=True, max_length=150)
    active = models.BooleanField(default=True, blank=True)

    class Meta:
        managed = True
        db_table = 'location'

    @staticmethod
    def lookup(locName):
        if locName is None:
            return None
        location = Location.objects.filter(name=locName).first()
        if not location:
            raise ValidationError({"errorCode":"SPEC-M12", "error": f"Location: {locName} does not exist."})
        return location

    @staticmethod
    def lookupOrCreate(locName):
        if locName is None:
            return None
        location = Location.objects.filter(name=locName).first()
        if location:
            return location
        return Location.objects.create(name=locName)

class Spec(models.Model):
    num = models.IntegerField()
    ver = models.CharField(max_length=50)
    title = models.CharField(max_length=4000)
    doc_type = models.ForeignKey(DocType, on_delete=models.PROTECT, related_name='+')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='+')
    keywords = models.CharField(max_length=4000, blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='+', null=True)
    state = models.CharField(max_length=50)
    created_by = models.ForeignKey(DjangoUser, on_delete=models.PROTECT, related_name='+')
    create_dt = models.DateTimeField()
    mod_ts = models.DateTimeField()
    jira = models.CharField(max_length=50, blank=True, null=True)
    anon_access = models.BooleanField(default=False)
    reason = models.CharField(max_length=4000, blank=True, null=True)
    approved_dt = models.DateTimeField(null=True)
    sunset_extended_dt = models.DateTimeField(null=True)

    class Meta:
        managed = True
        db_table = 'spec'
        unique_together = (('num', 'ver'),)

    @property
    def sunset_dt(self):
        if self.state == 'Active' and self.doc_type.sunset_interval:
            if self.sunset_extended_dt:
                return self.sunset_extended_dt + self.doc_type.sunset_interval
            elif self.approved_dt:
                return self.approved_dt + self.doc_type.sunset_interval
        return None

    @property
    def sunset_warn_dt(self):
        if self.sunset_dt and self.doc_type.sunset_warn:
            return self.sunset_dt - self.doc_type.sunset_warn
        return None

    def checkEditable(self, user):
        if self.state != "Draft" and not user.is_superuser:
            raise ValidationError({"errorCode":"SPEC-M07", "error": f"Spec is not in Draft state, it cannot be edited."})

        return

    def checkSunset(self):
        """If Active spec is past sunset date, set to Obsolete"""
        if self.state == 'Active':
            if self.sunset_dt and self.sunset_dt < timezone.now():
                self.state = 'Obsolete'
                self.save()
                SpecHist.objects.create(
                    spec=self,
                    mod_ts = timezone.now(),
                    upd_by = SpecUser.getSystemUser(),
                    change_type = 'Sunset',
                    comment = 'Spec has passed its sunset date and has been obsoleted by the system.'
                )

    @staticmethod
    def lookup(num, ver, user):
        if ver != "*":
            try:
                spec = Spec.objects.get(num=num, ver=ver)
                spec.checkSunset()
            except Spec.DoesNotExist:
                raise ValidationError({"errorCode":"SPEC-M04", "error": f"Spec ({num}/{ver}) does not exist."})
        else:
            try:
                spec = Spec.objects.get(num=num, state="Active")
                spec.checkSunset()
                if spec.state != 'Active':
                    raise Spec.DoesNotExist()
            except Spec.DoesNotExist:
                raise ValidationError({"errorCode":"SPEC-M06", "error": f"No active version of Spec ({num})."})

        if not user.is_authenticated and ( not spec.anon_access or spec.state != "Active"):
            raise ValidationError({"errorCode":"SPEC-M08", "error": f"spec {spec.num}-{spec.ver} cannot read without logging in."})
        if spec.doc_type.confidential:
            if not spec.department.isReader(user):
                if spec.state != "Draft" or user != spec.created_by:
                    raise ValidationError({"errorCode":"SPEC-M05", "error": f"User {user} cannot read confidential specs in department {spec.department}."})
        return spec

class SpecSig(models.Model):
    spec = models.ForeignKey(Spec, on_delete=models.CASCADE, related_name='sigs')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='+')
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+', blank=True, null=True)
    delegate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+', blank=True, null=True)
    signed_dt = models.DateTimeField(blank=True, null=True)
    from_am = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'spec_sig'
        unique_together = (('spec', 'role', 'signer'),)

class SpecHist(models.Model):
    spec = models.ForeignKey(Spec, on_delete=models.CASCADE, related_name='hist')
    mod_ts = models.DateTimeField()
    upd_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    change_type = models.CharField(max_length=50)
    comment = models.CharField(max_length=4000)

    class Meta:
        managed = True
        db_table = 'spec_hist'

class SpecFile(models.Model):
    spec = models.ForeignKey(Spec, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=4000)
    file = models.FileField(blank=True, null=True)
    seq = models.IntegerField()
    incl_pdf = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'spec_file'
        unique_together = (('spec', 'filename'),)

    @staticmethod
    def lookup(num, ver, fileName, request):
        spec = Spec.lookup(num, ver, request.user)

        state = request.GET.get('state') if request.GET.get('state') else 'Active'
        if state != spec.state:
            raise ValidationError({"errorCode":"SPEC-M11", "error": f"Spec ({num}/{ver}) is {spec.state}, not in {state} state."})

        if fileName is None:
            fileName = "*"
            specFile = spec.files.order_by('seq').first()
        else:
            specFile = spec.files.filter(filename=fileName).first()
        if specFile is not None:
            return specFile
        raise ValidationError({"errorCode":"SPEC-M09", "error": f"File {fileName} is not attached to spec ({num}/{ver})."})

class SpecReference(models.Model):
    spec = models.ForeignKey(Spec, on_delete=models.CASCADE, related_name='refs')
    num = models.IntegerField()
    ver = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'spec_reference'
