# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.transaction import atomic
from shuup.admin.form_part import FormPartsViewMixin, SaveFormPartsMixin
from shuup.admin.utils.views import CreateOrUpdateView

from shuup_api_permission.admin_module.form_parts import (
    AnonymousPermissionFormPart, APIAccessFormPart, APIPermissionGroupsFormPart,
    PermissionGroupsFormPart
)
from shuup_api_permission.admin_module.forms import (
    APIAccessForm, APIPermissionGroupsForm
)
from shuup_api_permission.models import APIAccess, APIPermissionGroups


class APIAccessEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = APIAccess
    form_class = APIAccessForm
    template_name = "shuup_api_permission/api_access_edit.jinja"
    context_object_name = "api_access"
    base_form_part_classes = [
        APIAccessFormPart,
        AnonymousPermissionFormPart
    ]

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)


class APIPermissionGroupsEditView(SaveFormPartsMixin, FormPartsViewMixin, CreateOrUpdateView):
    model = APIPermissionGroups
    form_class = APIPermissionGroupsForm
    template_name = "shuup_api_permission/permission_groups_edit.jinja"
    context_object_name = "api_permission_groups"
    base_form_part_classes = [
        APIPermissionGroupsFormPart,
        PermissionGroupsFormPart
    ]

    @atomic
    def form_valid(self, form):
        return self.save_form_parts(form)
