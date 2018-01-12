# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework_jwt.settings import api_settings

from shuup_api_permission.utils import get_jwt_from_request, get_jwt_payload

jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class APITokenAuthentication(BaseAuthentication):
    www_authenticate_realm = 'api'

    def authenticate(self, request):
        """
        Returns a two-tuple of `User` and token if a valid signature has been
        supplied using JWT-based authentication.  Otherwise returns `None`.
        """
        payload = getattr(request, "jwt_payload", None)
        jwt_value = getattr(request, "jwt_value", None)
        if not payload:
            jwt_value = get_jwt_from_request(request)
            payload = get_jwt_payload(jwt_value)

        if not payload:
            return None

        user = self.authenticate_credentials(payload)
        if not user:
            return None

        return (user, jwt_value)

    def authenticate_credentials(self, payload):
        """
        Returns an active user that matches the payload's user id and email.
        """
        user_model = get_user_model()
        username = jwt_get_username_from_payload(payload)

        # No user inside token
        if not username:
            return None

        try:
            user = user_model.objects.get_by_natural_key(username)
        except user_model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid signature.'))

        if not user.is_active:
            raise exceptions.AuthenticationFailed(_('User account is disabled.'))

        return user

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return '{0} realm="{1}"'.format(api_settings.JWT_AUTH_HEADER_PREFIX, self.www_authenticate_realm)
