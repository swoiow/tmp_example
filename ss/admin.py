#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin

from . import models


class BillboardAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created")
    search_fields = ("title", "content")


admin.site.register(models.Billboard, BillboardAdmin)
