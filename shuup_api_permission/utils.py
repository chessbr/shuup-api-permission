# -*- coding: utf-8 -*-
import jwt
from django.db.models import Q
from django.utils.encoding import smart_text
from django.utils.lru_cache import lru_cache
from django.utils.translation import ugettext as _
from rest_framework import exceptions
from rest_framework.authentication import get_authorization_header
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.utils import \
    jwt_payload_handler as base_jwt_payload_handler
from rest_jwt_permission.settings import get_setting

jwt_decode_handler = api_settings.JWT_DECODE_HANDLER


def get_jwt_from_request(request):
    auth = get_authorization_header(request).split()
    auth_header_prefix = api_settings.JWT_AUTH_HEADER_PREFIX.lower()

    if not auth:
        if api_settings.JWT_AUTH_COOKIE:
            return request.COOKIES.get(api_settings.JWT_AUTH_COOKIE)
        return None

    if smart_text(auth[0].lower()) != auth_header_prefix:
        return None

    if len(auth) == 1:
        msg = _('Invalid Authorization header. No credentials provided.')
        raise exceptions.PermissionDenied(msg)
    elif len(auth) > 2:
        msg = _('Invalid Authorization header. Credentials string should not contain spaces.')
        raise exceptions.PermissionDenied(msg)

    return auth[1]


@lru_cache()
def get_jwt_payload(jwt_value):
    if not jwt_value:
        raise exceptions.PermissionDenied(_('Missing access token.'))
    try:
        return jwt_decode_handler(jwt_value)
    except jwt.ExpiredSignature:
        raise exceptions.PermissionDenied(_('Signature has expired.'))
    except jwt.DecodeError:
        raise exceptions.PermissionDenied(_('Error decoding signature.'))
    except jwt.InvalidTokenError:
        raise exceptions.PermissionDenied()


def jwt_payload_handler(user, api_access, shop):
    payload = base_jwt_payload_handler(user)

    if user.is_authenticated():
        user_groups_filter = Q()
        for group in user.groups.all():
            user_groups_filter |= Q(groups=group)

        permissions = list(
            api_access.permissions_groups
            .filter(user_groups_filter)
            .values_list("permissions__identifier", flat=True)
            .distinct()
        )
    else:
        permissions = list(api_access.anonymous_permissions.values_list("identifier", flat=True).distinct())

    payload["anonymous"] = not user.is_authenticated()
    payload["api_key"] = api_access.key
    payload["shop"] = shop.id
    payload[get_setting("JWT_PAYLOAD_SCOPES_KEY")] = [permission for permission in permissions if permission]
    return payload
