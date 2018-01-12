# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from shuup_api_permission.utils import get_jwt_from_request, get_jwt_payload


class ShuupAPIPermissionMiddleware(object):
    """
    Read the JWT from the request and the payload as a request attribute
    This will just cache the JWT payload into the request
    """
    def process_request(self, request):
        jwt = get_jwt_from_request(request)
        if jwt:
            payload = get_jwt_payload(jwt)
            request.jwt_payload = payload
            request.jwt_value = jwt
