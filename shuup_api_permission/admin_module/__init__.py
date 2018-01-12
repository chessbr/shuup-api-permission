# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls

from shuup_api_permission.models import APIAccess, APIPermissionGroups


class APIAccessModule(AdminModule):
    name = _("API Access")
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shuup_admin:api_access.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^api_access",
            view_template="shuup_api_permission.admin_module.views.APIAccess%sView",
            name_template="api_access.%s",
            permissions=get_default_model_permissions(APIAccess)
        )

    def get_menu_category_icons(self):
        return {self.name: "fa fa-bolt"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("API Access"),
                icon="fa fa-bolt",
                url="shuup_admin:api_access.list",
                category=SETTINGS_MENU_CATEGORY,
                subcategory="other_settings",
                ordering=10
            )
        ]

    def get_required_permissions(self):
        return get_default_model_permissions(APIAccess)

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(APIAccess, "shuup_admin:api_access", object, kind)


class APIPermissionGroupsModule(AdminModule):
    name = _("API Permissions")
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shuup_admin:api_permission_groups.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^api_permission_groups",
            view_template="shuup_api_permission.admin_module.views.APIPermissionGroups%sView",
            name_template="api_permission_groups.%s",
            permissions=get_default_model_permissions(APIPermissionGroups)
        )

    def get_menu_category_icons(self):
        return {self.name: "fa fa-bolt"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("API Permissions"),
                icon="fa fa-bolt",
                url="shuup_admin:api_permission_groups.list",
                category=SETTINGS_MENU_CATEGORY,
                subcategory="other_settings",
                ordering=11
            )
        ]

    def get_required_permissions(self):
        return get_default_model_permissions(APIPermissionGroups)

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(APIPermissionGroups, "shuup_admin:api_permission_groups", object, kind)
