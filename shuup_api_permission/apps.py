# -*- coding: utf-8 -*-
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup_api_permission"
    verbose_name = "Shuup API Permissions"
    provides = {
        "admin_module": [
            "shuup_api_permission.admin_module:APIAccessModule",
            "shuup_api_permission.admin_module:APIPermissionGroupsModule"
        ],
        "api_populator": [
            "shuup_api_permission.api:populate_api"
        ]
    }
