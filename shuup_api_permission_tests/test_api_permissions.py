# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import AnonymousUser, Group
from rest_framework.test import APIRequestFactory
from rest_framework_jwt.utils import jwt_encode_handler
from rest_jwt_permission.utils import get_role_for, get_view_role
from shuup.core import cache
from shuup.core.api.shop import ShopViewSet
from shuup.testing import factories

from shuup_api_permission.models import APIPermissionGroups, APIPermissionScope
from shuup_api_permission.permissions import (
    API_ACCESS_CACHE_KEY_FMT, APIAccessPermission, APIScopePermission
)
from shuup_api_permission.utils import get_jwt_payload, jwt_payload_handler

from . import create_random_api_access


def setup_function(fn):
    get_jwt_payload.cache_clear()
    cache.clear()


@pytest.mark.django_db
def test_api_access_permission():
    shop = factories.get_default_shop()
    api_access_permission = APIAccessPermission()
    factory = APIRequestFactory()

    def get_request(jwt, shop):
        request = factory.get('/api/shuup/shop/')
        request.META["HTTP_AUTHORIZATION"] = "JWT %s" % jwt
        request.shop = shop
        return request

    # no API Key
    jwt = jwt_encode_handler({})
    request = get_request(jwt, shop)
    assert api_access_permission.has_permission(request, None) is False

    # invalid API Key
    jwt = jwt_encode_handler({"api_key": "qwerty"})
    request = get_request(jwt, shop)
    assert api_access_permission.has_permission(request, None) is False

    # valid api key, but disabled
    api_access = create_random_api_access(enabled=False)
    jwt = jwt_encode_handler({"api_key": api_access.key})
    request = get_request(jwt, shop)
    assert api_access_permission.has_permission(request, None) is False

    # finally, valid api key
    api_access = create_random_api_access()
    jwt = jwt_encode_handler({"api_key": api_access.key})
    request = get_request(jwt, shop)
    assert api_access_permission.has_permission(request, None)

    # the api_access shoud be cached
    assert cache.get(API_ACCESS_CACHE_KEY_FMT.format(shop=shop.id, key=api_access.key)).id == api_access.id


@pytest.mark.parametrize("authenticated", [True, False])
def test_api_scope_permissions(admin_user, authenticated):
    shop = factories.get_default_shop()
    api_access_permission = APIScopePermission()
    factory = APIRequestFactory()

    user = admin_user if authenticated else AnonymousUser()

    def get_request_view(jwt, shop):
        request = factory.get('/api/shuup/shop/')
        request.META["HTTP_AUTHORIZATION"] = "JWT %s" % jwt
        request.shop = shop
        request.user = user
        view = ShopViewSet(action="list", method="get")
        return request, view

    # no API Key
    jwt = jwt_encode_handler({})
    request, view = get_request_view(jwt, shop)
    assert api_access_permission.has_permission(request, view) is False

    # no scopes for anonymous user
    api_access = create_random_api_access()
    payload = jwt_payload_handler(user, api_access, shop=shop)
    assert payload["scopes"] == []
    request, view = get_request_view(jwt_encode_handler(payload), shop)
    assert api_access_permission.has_permission(request, view) is False

    # add the permission for ShopViewSet.list on anonymous, OK
    api_access = create_random_api_access(enabled=False)
    scope = get_view_role(ShopViewSet, get_role_for("get", "list"))

    permission = APIPermissionScope.objects.get_or_create(identifier=scope)[0]
    if authenticated:
        group = Group.objects.create(name="g1")
        admin_user.groups.add(group)
        api_permission_groups = APIPermissionGroups.objects.create(name="schema 1")
        api_permission_groups.groups.add(group)
        api_permission_groups.permissions.add(permission)
        api_access.permissions_groups.add(api_permission_groups)
    else:
        api_access.anonymous_permissions.add(permission)

    payload = jwt_payload_handler(user, api_access, shop=shop)
    assert len(payload["scopes"]) == 1
    assert payload["scopes"][0] == scope
    request, view = get_request_view(jwt_encode_handler(payload), shop)
    assert api_access_permission.has_permission(request, view)


def test_api_scope_permission_multiple_groups(admin_user):
    shop = factories.get_default_shop()
    api_access_permission = APIScopePermission()
    factory = APIRequestFactory()

    def get_request_view(jwt, shop):
        request = factory.get('/api/shuup/shop/')
        request.META["HTTP_AUTHORIZATION"] = "JWT %s" % jwt
        request.shop = shop
        request.user = admin_user
        view = ShopViewSet(action="list", method="get")
        return request, view

    api_access = create_random_api_access()

    scope = get_view_role(ShopViewSet, get_role_for("get", "list"))
    permission = APIPermissionScope.objects.get_or_create(identifier=scope)[0]

    group1 = Group.objects.create(name="g1")
    group2 = Group.objects.create(name="g2")

    admin_user.groups.add(group1)
    admin_user.groups.add(group2)

    api_permission_groups1 = APIPermissionGroups.objects.create(name="schema 1")
    api_permission_groups2 = APIPermissionGroups.objects.create(name="schema 2")

    api_permission_groups1.groups.add(group1)
    api_permission_groups2.groups.add(group2)

    # only add permission on group2
    api_permission_groups2.permissions.add(permission)

    api_access.permissions_groups.add(api_permission_groups1)
    api_access.permissions_groups.add(api_permission_groups2)

    payload = jwt_payload_handler(admin_user, api_access, shop=shop)
    assert len(payload["scopes"]) == 1
    assert payload["scopes"][0] == scope
    request, view = get_request_view(jwt_encode_handler(payload), shop)
    assert api_access_permission.has_permission(request, view)
