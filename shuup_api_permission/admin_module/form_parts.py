# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from shuup.admin.form_part import FormPart, TemplatedFormDef

from shuup_api_permission.admin_module.forms import (
    APIAccessForm, APIPermissionGroupsForm, APIPermissionsForm
)
from shuup_api_permission.models import APIPermissionScope


class APIAccessFormPart(FormPart):
    priority = -1000

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            APIAccessForm,
            template_name="shuup_api_permission/api_access_form_part.jinja",
            required=True,
            kwargs={
                "instance": self.object,
                "request": self.request
            }
        )

    def form_valid(self, form_group):
        self.object = form_group["base"].save()
        return self.object


class APIPermissionGroupsFormPart(FormPart):
    priority = -1000

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            APIPermissionGroupsForm,
            template_name="shuup_api_permission/permission_groups_form_part.jinja",
            required=True,
            kwargs={
                "instance": self.object,
                "request": self.request
            }
        )

    def form_valid(self, form_group):
        self.object = form_group["base"].save()
        return self.object


class AnonymousPermissionFormPart(FormPart):
    priority = 1
    title = _("Anonymous permissions")

    def get_form_defs(self):
        initial = []
        if self.object.pk:
            initial = self.object.anonymous_permissions.values_list("identifier", flat=True)

        yield TemplatedFormDef(
            "permissions",
            APIPermissionsForm,
            template_name="shuup_api_permission/permissions_form_part.jinja",
            required=False,
            kwargs={"title": self.title, "initial": initial}
        )

    def form_valid(self, form_group):
        self.object.anonymous_permissions.clear()
        for scope in form_group["permissions"].get_scopes():
            self.object.anonymous_permissions.add(APIPermissionScope.objects.get_or_create(identifier=scope)[0])
        return self.object


class PermissionGroupsFormPart(FormPart):
    priority = 1
    title = _("Permissions")

    def get_form_defs(self):
        initial = []
        if self.object.pk:
            initial = self.object.permissions.values_list("identifier", flat=True)

        yield TemplatedFormDef(
            "permissions",
            APIPermissionsForm,
            template_name="shuup_api_permission/permissions_form_part.jinja",
            required=False,
            kwargs={"title": self.title, "initial": initial}
        )

    def form_valid(self, form_group):
        self.object.permissions.clear()
        for scope in form_group["permissions"].get_scopes():
            self.object.permissions.add(APIPermissionScope.objects.get_or_create(identifier=scope)[0])
        return self.object
