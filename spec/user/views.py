from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.dev_utils import formatError, IsSuperUser
from user.authentication import token_expire_handler
from user.serializers import TokenSerializer
from proj.util import MyLDAPBackend

class UserToken(APIView):
    """
    get:
    See a list of current tokens and their expiration

    post:
    Generate a new token for the authenticated user and return it.

    delete:
    Invalidate token for authenticated user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        try:
            tokens = Token.objects.raw("""
                            select t.*
                            from authtoken_token t
                            inner join auth_user u
                            on t.user_id = u.id
                            order by u.username""")
            serializer = TokenSerializer(tokens, many=True)
            return Response(serializer.data)
        except BaseException as be:  # pragma: no cover
            formatError(be, "TOKEN-001")


class AdminToken(APIView):
    """
    post:
    Generate a new token for the specified user and return it.

    delete:
    Invalidate token for specified user
    """
    permission_classes = [IsSuperUser]

    def post(self, request, username, format=None):
        try:
            if settings.AUTH_LDAP_SERVER_URI is not None and len(settings.AUTH_LDAP_SERVER_URI) > 1: #pragma nocover Only one of these branches can be reasonably tested.
                user = MyLDAPBackend().populate_user(username)
            else: #pragma nocover Only one of these branches can be reasonably tested.
                user = User.objects.filter(username=username).first()
            if user is None:
                raise ValidationError(
                    {"errorCode": "TOKEN-004", "error": f"Specified user: {username} does not exist."})

            token, _ = Token.objects.get_or_create(user=user)
            _, token = token_expire_handler(token)

            return Response({"Authorization": token.key})
        except BaseException as be:  # pragma: no cover
            formatError(be, "TOKEN-005")

    def delete(self, request, username, format=None):
        try:
            user = User.objects.filter(username=username).first()
            if user is None:
                raise ValidationError(
                    {"errorCode": "TOKEN-006", "error": f"Specified user: {username} does not exist."})
            token = Token.objects.filter(user=user).first()
            if token is not None:
                token.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BaseException as be:  # pragma: no cover
            formatError(be, "TOKEN-007")


class GetUser(APIView):
    """
    Return user info.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        try:
            token = Token.objects.filter(user=request.user).first()
            ret = {
                "user": request.user.username,
                "is_admin": request.user.is_superuser,
                "is_readAll": request.user.is_superuser,
            }
            return Response(ret)
        except BaseException as be:  # pragma: no cover
            formatError(be, "TOKEN-008")