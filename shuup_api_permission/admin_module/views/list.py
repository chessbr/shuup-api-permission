# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from shuup.admin.utils.picotable import Column, TextFilter
from shuup.admin.utils.views import PicotableListView

from shuup_api_permission.models import APIAccess, APIPermissionGroups


class APIAccessListView(PicotableListView):
    model = APIAccess
    default_columns = [
        Column(
            "name",
            _("Name"),
            sort_field="name",
            display="name",
            filter_config=TextFilter(
                filter_field="name",
                placeholder=_("Filter by name...")
            )
        ),
        Column(
            "key",
            _("Key"),
            filter_config=TextFilter(
                filter_field="key",
                placeholder=_("Filter by key...")
            )
        ),
        Column("enabled", _("Enabled"))
    ]


class APIPermissionGroupsListView(PicotableListView):
    model = APIPermissionGroups
    default_columns = [
        Column(
            "name",
            _("Name"),
            sort_field="name",
            display="name",
            filter_config=TextFilter(
                filter_field="name",
                placeholder=_("Filter by name...")
            )
        )
    ]
