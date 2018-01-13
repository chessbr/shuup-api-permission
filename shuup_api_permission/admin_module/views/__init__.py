# -*- coding: utf-8 -*-
from .edit import APIAccessEditView, APIPermissionGroupsEditView
from .list import APIAccessListView, APIPermissionGroupsListView

__all__ = [
    "APIAccessEditView",
    "APIAccessListView",
    "APIPermissionGroupsEditView",
    "APIPermissionGroupsListView"
]
