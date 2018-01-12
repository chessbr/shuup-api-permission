# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib.auth.models import Group as PermissionGroup
from django.core.urlresolvers import reverse_lazy
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from rest_jwt_permission.providers.api_endpoint import APIEndpointScopeProvider
from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.forms.widgets import QuickAddRelatedObjectMultiSelect
from shuup.api.mixins import PermissionHelperMixin

from shuup_api_permission.models import APIAccess, APIPermissionGroups


class QuickAddAPIPermissionGroupsMultiSelect(QuickAddRelatedObjectMultiSelect):
    url = reverse_lazy("shuup_admin:api_permission_groups.new")


class ShopBasedModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.shop = self.request.shop
        super(ShopBasedModelForm, self).__init__(*args, **kwargs)


class APIPermissionsForm(forms.Form):
    api_view_prefix = "apiview__"

    def __init__(self, *args, **kwargs):
        self.title = kwargs.pop("title", None)
        initial = kwargs.pop("initial", [])

        super(APIPermissionsForm, self).__init__(*args, **kwargs)

        scopes = APIEndpointScopeProvider().get_available_scopes()
        api_scopes = {}

        # group API endpoint scopes
        for scope in scopes:
            if scope.view_class not in api_scopes:
                api_scopes[scope.view_class] = []
            api_scopes[scope.view_class].append(scope)

        sorted_viewsets = sorted(api_scopes.keys(), key=lambda a: a.__name__)

        # now add fields for API endpoints
        for viewset in sorted_viewsets:
            scopes = api_scopes[viewset]
            choices = [(scope.identifier, "{}: {}".format(scope.method.upper(), scope.path)) for scope in scopes]

            viewset_instance = viewset()
            label = viewset_instance.get_view_name() or viewset.__name__

            help_text = "Module: {}".format(viewset.__module__)
            if issubclass(viewset, PermissionHelperMixin):
                help_text = "{}. {}".format(help_text, viewset_instance.get_help_text())

            choices_ids = [choice[0] for choice in choices]
            self.fields["{}{}".format(self.api_view_prefix, viewset.__name__)] = forms.MultipleChoiceField(
                required=False,
                label=label,
                help_text=help_text,
                choices=choices,
                initial=[v for v in initial if v in choices_ids]
            )

    def get_scopes(self):
        for key, scopes in self.cleaned_data.items():
            if key.startswith(self.api_view_prefix):
                for scope in scopes:
                    yield scope


class APIAccessForm(ShopBasedModelForm):
    class Meta:
        model = APIAccess
        exclude = ("anonymous_permissions",)
        widgets = {
            "permissions_groups": QuickAddAPIPermissionGroupsMultiSelect()
        }

    def __init__(self, *args, **kwargs):
        super(APIAccessForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["key"] = forms.CharField(
                initial=self.instance.key,
                required=False,
                widget=forms.TextInput(
                    attrs={
                        "readonly": "readonly",
                        "placeholder": _("Auto generated key")
                    }
                )
            )
            self.fields["secret"] = forms.CharField(
                initial=self.instance.secret,
                required=False,
                widget=forms.TextInput(
                    attrs={
                        "readonly": "readonly",
                        "placeholder": _("Auto generated secret")
                    }
                )
            )


class APIPermissionGroupsForm(ShopBasedModelForm):
    class Meta:
        model = APIPermissionGroups
        exclude = ("permissions",)

    def __init__(self, *args, **kwargs):
        super(APIPermissionGroupsForm, self).__init__(*args, **kwargs)

        initial_groups = []
        if self.instance.pk and hasattr(self.instance, "groups"):
            initial_groups = self.instance.groups.all()

        self.fields["groups"] = Select2MultipleField(
            model=PermissionGroup,
            initial=[group.pk for group in initial_groups],
            label=_("Permission Groups")
        )
        self.fields["groups"].widget.choices = [(group.pk, force_text(group)) for group in initial_groups]
