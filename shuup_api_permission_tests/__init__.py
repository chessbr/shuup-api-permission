# -*- coding: utf-8 -*-

def create_random_api_access(**kwargs):
    from shuup.testing import factories
    from shuup_api_permission.models import APIAccess
    params = {
        "name": "API Access",
        "enabled": True
    }
    params.update(kwargs or {})
    api_access = APIAccess(**params)
    api_access.full_clean()
    api_access.save()
    return api_access
