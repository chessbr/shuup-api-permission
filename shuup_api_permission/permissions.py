# -*- coding: utf-8 -*-
from rest_framework import permissions
from rest_jwt_permission.settings import get_imported_setting
from rest_jwt_permission.utils import get_role_for, get_view_role
from shuup.core import cache

from shuup_api_permission.models import APIAccess
from shuup_api_permission.utils import get_jwt_from_request, get_jwt_payload

API_ACCESS_CACHE_KEY_FMT = "api_access_{key}"


class APIAccessPermission(permissions.BasePermission):
    """
    Make sure each request contains a valid JWT with a valid API Key
    """

    def has_permission(self, request, view):
        payload = getattr(request, "jwt_payload", None)
        if not payload:
            payload = get_jwt_payload(get_jwt_from_request(request))

        api_key = payload.get("api_key")
        if not api_key:
            return False

        api_access_cache_key = API_ACCESS_CACHE_KEY_FMT.format(key=api_key)
        api_access = cache.get(api_access_cache_key)

        if not api_access:
            try:
                api_access = APIAccess.objects.get(key=api_key)
                cache.set(api_access_cache_key, api_access)
            except APIAccess.DoesNotExist:
                return False

        return api_access.enabled


class APIScopePermission(permissions.BasePermission):
    """
    Make sure the user has the proper scope permission inside the JWT
    Based on rest_jwt_permission.permissions.JWTAPIPermission
    """

    def has_permission(self, request, view):
        payload = getattr(request, "jwt_payload", None)
        if not payload:
            payload = get_jwt_payload(get_jwt_from_request(request))

        if not payload:
            return False

        get_scopes_from_payload = get_imported_setting("GET_SCOPES_FROM_PAYLOAD_HANDLER")
        payload_scopes = get_scopes_from_payload(payload)
        role = get_role_for(request.method.lower(), getattr(view, "action", None))
        scope = get_view_role(view, role)
        return scope in payload_scopes
