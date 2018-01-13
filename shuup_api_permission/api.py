# -*- coding: utf-8 -*-
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import exceptions, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from shuup_api_permission.serializers import (
    JSONWebTokenSerializer, RefreshJSONWebTokenSerializer,
    VerifyJSONWebTokenSerializer
)

jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER


class APIAuthView(viewsets.GenericViewSet):
    queryset = get_user_model().objects.none()
    serializer_class = JSONWebTokenSerializer
    permission_classes = ()
    authentication_classes = ()

    def get_serializer_class(self):
        if self.action == "create":
            return JSONWebTokenSerializer
        elif self.action == "refresh":
            return RefreshJSONWebTokenSerializer
        elif self.action == "verify":
            return VerifyJSONWebTokenSerializer
        raise exceptions.NotFound()

    def create(self, request, *args, **kwargs):
        return self.token_auth_refresh(request)

    @list_route(methods=["post"])
    def refresh(self, request):
        return self.token_auth_refresh(request)

    @list_route(methods=["post"])
    def verify(self, request):
        return self.token_auth_refresh(request)

    def token_auth_refresh(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(True)
        user = serializer.object.get('user')
        token = serializer.object.get('token')
        response_data = jwt_response_payload_handler(token, user, request)
        response = Response(response_data)

        if api_settings.JWT_AUTH_COOKIE:
            expiration = (datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA)
            response.set_cookie(api_settings.JWT_AUTH_COOKIE, token, expires=expiration, httponly=True)

        return response


def populate_api(router):
    router.register(settings.SHUUP_API_AUTH_URL, APIAuthView)
