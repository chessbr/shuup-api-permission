# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIClient
from rest_jwt_permission.utils import get_role_for, get_view_role
from shuup.core.api.front_users import FrontUserViewSet
from shuup.core.api.shop import ShopViewSet
from shuup.testing import factories

from shuup_api_permission.models import APIPermissionGroups, APIPermissionScope
from shuup_api_permission.utils import get_jwt_payload

from . import create_random_api_access


def setup_function(fn):
    get_jwt_payload.cache_clear()


@pytest.mark.django_db
def test_api_token():
    """
    Test whether the API returns the access token correctly
    """
    shop = factories.get_default_shop()
    user = factories.create_random_user()
    password = "admin"
    user.set_password(password)
    user.save()
    group = Group.objects.create(name="group 1")

    client = APIClient()

    api_access = create_random_api_access()
    # try logging without the api access credentials
    response = client.post("/api/auth/", format="json", data={
        "username": user.username,
        "password": password
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.post("/api/auth/", format="json", data={
        "username": user.username,
        "password": password,
        "api_key": api_access.key,
        "api_secret": api_access.secret
    })
    assert response.status_code == status.HTTP_200_OK
    jwt = response.data["token"]

    client.credentials(HTTP_AUTHORIZATION="JWT " + jwt)

    # add permission for the user group
    scope = get_view_role(FrontUserViewSet, get_role_for("get", "retrieve"))
    permission_groups = APIPermissionGroups.objects.create(
        name="special group"
    )
    permission_groups.groups.add(group)
    permission_groups.permissions.add(APIPermissionScope.objects.get_or_create(identifier=scope)[0])
    user.groups.add(group)
    api_access.permissions_groups.add(permission_groups)

    # refresh the token to include the new permission
    response = client.post("/api/auth/refresh/", format="json", data={"token": jwt})
    assert response.status_code == status.HTTP_200_OK
    jwt = response.data["token"]
    client.credentials(HTTP_AUTHORIZATION="JWT " + jwt)

    # fetch user data
    response = client.get("/api/shuup/front/user/me/", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == user.id

    # verify token
    client.credentials(HTTP_AUTHORIZATION="")
    response = client.post("/api/auth/verify/", format="json", data={"token": jwt})
    assert response.status_code == status.HTTP_200_OK

    # disable the key
    api_access.enabled = False
    api_access.save()

    client.credentials(HTTP_AUTHORIZATION="JWT " + jwt)
    response = client.get("/api/shuup/front/user/me/", format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_open_api():
    """
    Test whether open API's (without authentication) can be accessed
    """
    shop = factories.get_default_shop()
    client = APIClient()

    response = client.get("/api/shuup/shop/%d/" % shop.id)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    api_access = create_random_api_access()
    response = client.post("/api/auth/", format="json", data={
        "api_key": api_access.key,
        "api_secret": api_access.secret
    })
    assert response.status_code == status.HTTP_200_OK
    jwt = response.data["token"]

    client.credentials(HTTP_AUTHORIZATION="JWT " + jwt)

    # no permission for shop API
    response = client.get("/api/shuup/shop/%d/" % shop.id)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # add permission for anonymous
    scope = get_view_role(ShopViewSet, get_role_for("get", "retrieve"))
    api_access.anonymous_permissions.add(APIPermissionScope.objects.get_or_create(identifier=scope)[0])

    # refresh the token to include the new permission
    response = client.post("/api/auth/refresh/", format="json", data={
        "token": jwt
    })
    assert response.status_code == status.HTTP_200_OK
    jwt = response.data["token"]
    client.credentials(HTTP_AUTHORIZATION="JWT " + jwt)

    response = client.get("/api/shuup/shop/%d/" % shop.id)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == shop.id
