# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import AnonymousUser, Group
from django.utils.text import force_text
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory
from rest_framework_jwt.utils import jwt_encode_handler
from rest_jwt_permission.utils import get_role_for, get_view_role
from shuup.core.api.shop import ShopViewSet
from shuup.testing import factories

from shuup_api_permission.authentication import APITokenAuthentication
from shuup_api_permission.models import APIPermissionScope
from shuup_api_permission.utils import get_jwt_payload


def setup_function(fn):
    get_jwt_payload.cache_clear()


def test_api_authentication(admin_user):
    shop = factories.get_default_shop()
    authentication = APITokenAuthentication()
    factory = APIRequestFactory()

    def get_request(jwt, shop):
        request = factory.get('/api/shuup/shop/')
        request.META["HTTP_AUTHORIZATION"] = "JWT %s" % jwt
        request.shop = shop
        return request

    # no API Key
    jwt = jwt_encode_handler({})
    request = get_request(jwt, shop)
    assert authentication.authenticate(request) is None

    # invalid username
    jwt = jwt_encode_handler({"username": "qwerty"})
    request = get_request(jwt, shop)
    with pytest.raises(AuthenticationFailed):
        authentication.authenticate(request)

    # correct username
    jwt = jwt_encode_handler({"username": admin_user.username})
    request = get_request(jwt, shop)
    user, token = authentication.authenticate(request)
    assert user == admin_user
    assert force_text(token) == force_text(jwt)

    # user is not active
    admin_user.is_active = False
    admin_user.save()
    with pytest.raises(AuthenticationFailed):
        authentication.authenticate(request)
