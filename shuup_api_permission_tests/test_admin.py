# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_jwt_permission.utils import get_role_for, get_view_role
from shuup.core.api.front_users import FrontUserViewSet
from shuup.core.api.shop import ShopViewSet
from shuup.testing import factories
from shuup.testing.soup_utils import extract_form_fields

from shuup_api_permission.models import APIPermissionGroups, APIPermissionScope, APIAccess
from shuup_api_permission.utils import get_jwt_payload
from shuup_tests.utils import SmartClient, printable_gibberish

from . import create_random_api_access


def setup_function(fn):
    get_jwt_payload.cache_clear()


@pytest.mark.django_db
def test_create_api_access(rf, admin_user):
    shop = factories.get_default_shop()
    client = SmartClient()
    client.force_login(admin_user)

    url = reverse("shuup_admin:api_access.new")
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200

    inputs = extract_form_fields(soup)
    name = printable_gibberish()
    inputs["base-name"] = name
    inputs["base-enabled"] = False

    assert APIAccess.objects.count() == 0

    response = client.post(url, data=inputs)
    assert response.status_code == 302

    api_access = APIAccess.objects.first()
    assert api_access.enabled is False
    assert api_access.name == name

    edit_url = reverse("shuup_admin:api_access.edit", kwargs={"pk": api_access.pk})
    assert response.url == edit_url

    response, soup = client.response_and_soup(edit_url)
    assert response.status_code == 200
    inputs = extract_form_fields(soup)
    new_name = printable_gibberish()
    inputs["base-name"] = new_name
    inputs["base-enabled"] = True
    response = client.post(edit_url, data=inputs)
    assert response.status_code == 302
    assert response.url == edit_url

    api_access.refresh_from_db()
    assert api_access.enabled
    assert api_access.name == new_name


@pytest.mark.django_db
def test_create_api_permission_groups(rf, admin_user):
    shop = factories.get_default_shop()
    group1 = Group.objects.create(name="group1")
    group2 = Group.objects.create(name="group2")

    client = SmartClient()
    client.force_login(admin_user)

    url = reverse("shuup_admin:api_permission_groups.new")
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200

    inputs = extract_form_fields(soup)
    name = printable_gibberish()
    inputs["base-name"] = name
    inputs["base-groups"] = [group2.pk]

    assert APIPermissionGroups.objects.count() == 0

    response = client.post(url, data=inputs)
    assert response.status_code == 302

    permission_groups = APIPermissionGroups.objects.first()
    assert permission_groups.name == name
    assert permission_groups.groups.count() == 1
    assert group2 in permission_groups.groups.all()

    edit_url = reverse("shuup_admin:api_permission_groups.edit", kwargs={"pk": permission_groups.pk})
    assert response.url == edit_url

    response, soup = client.response_and_soup(edit_url)
    assert response.status_code == 200
    inputs = extract_form_fields(soup)
    new_name = printable_gibberish()
    inputs["base-name"] = new_name
    inputs["base-groups"] = [group2.pk, group1.pk]
    response = client.post(edit_url, data=inputs)
    assert response.status_code == 302
    assert response.url == edit_url

    permission_groups.refresh_from_db()
    assert permission_groups.name == new_name
    assert permission_groups.groups.count() == 2
    assert group1 in permission_groups.groups.all()
    assert group2 in permission_groups.groups.all()
