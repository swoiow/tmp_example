#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from . import models


class BillboardAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created")
    search_fields = ("title", "content")


class DockerExtraAdmin(admin.StackedInline):
    model = models.DockerExtra
    can_delete = False
    verbose_name_plural = '扩展配置'


class UserAdmin(BaseUserAdmin):
    inlines = (DockerExtraAdmin,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(models.Billboard, BillboardAdmin)

from os import environ


def get_ip_address():
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


environ["SERVER_IP"] = get_ip_address()
