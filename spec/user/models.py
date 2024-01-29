from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from rest_framework.exceptions import ValidationError
from proj.util import MyLDAPBackend

class User(DjangoUser):

    @staticmethod
    def lookup(username):
        user = DjangoUser.objects.filter(username=username).first()
        if not user:
            if settings.AUTH_LDAP_SERVER_URI is not None and len(settings.AUTH_LDAP_SERVER_URI) > 1: #pragma nocover Only one of these branches can be reasonably tested.
                user = MyLDAPBackend().populate_user(username)
        if not user:
            raise ValidationError({"errorCode":"USER-M01", "error": f"User: {username} does not exist."})
        if not user.is_active:
            raise ValidationError({"errorCode":"USER-M02", "error": f"User: {username} is not an active account."})
        return user

    @staticmethod
    def getSystemUser():
        """Return the system_user. If not present, make one and return it."""
        SYS_USERNAME='system_user'
        user = DjangoUser.objects.filter(username=SYS_USERNAME).first()
        if not user:
            user = DjangoUser.objects.create_user(
                username=SYS_USERNAME,
                password='xx'
            )
        return user
