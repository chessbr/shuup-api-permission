# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid1, uuid4

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from shuup.core import cache


@python_2_unicode_compatible
class APIPermissionScope(models.Model):
    identifier = models.CharField(max_length=250, unique=True, verbose_name=_("Permission scope identifier"))

    class Meta:
        verbose_name = _("API permission scope")
        verbose_name_plural = _("API permission scopes")

    def __str__(self):
        return self.identifier


@python_2_unicode_compatible
class APIPermissionGroups(models.Model):
    name = models.CharField(max_length=60, verbose_name=_("name"))
    groups = models.ManyToManyField("auth.Group", verbose_name=_("groups"), related_name="api_permissions")
    permissions = models.ManyToManyField(APIPermissionScope, blank=True, verbose_name=_("permissions"))

    class Meta:
        verbose_name = _("API permission group")
        verbose_name_plural = _("API permissions groups")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class APIAccess(models.Model):
    key = models.CharField(max_length=128, verbose_name=_("key"), unique=True, editable=False)
    secret = models.CharField(max_length=128, verbose_name=_("secret"), editable=False)
    name = models.CharField(max_length=60, verbose_name=_("name"))
    enabled = models.BooleanField(default=True, verbose_name=_("enabled"))
    anonymous_permissions = models.ManyToManyField(
        APIPermissionScope,
        blank=True,
        verbose_name=_("anonymous permissions")
    )
    permissions_groups = models.ManyToManyField(
        APIPermissionGroups,
        blank=True,
        verbose_name=_("API permission groups")
    )

    class Meta:
        verbose_name = _("API access")
        verbose_name_plural = _("API accesses")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = uuid1().hex
        if not self.secret:
            self.secret = "{}{}".format(uuid4().hex, uuid4().hex)

        if self.pk:
            from shuup_api_permission.permissions import API_ACCESS_CACHE_KEY_FMT
            api_access_cache_key = API_ACCESS_CACHE_KEY_FMT.format(key=self.key)
            cache.bump_version(api_access_cache_key)

        super(APIAccess, self).save(*args, **kwargs)
