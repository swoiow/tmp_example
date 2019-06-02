#!/usr/bin/env python
# -*- coding: utf-8 -*

import json
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import DEFERRED


class Billboard(models.Model):
    DRAFT = 0
    PUBLIC = 1
    STATUS_CHOICES = (
        (DRAFT, "DRAFT"),
        (PUBLIC, "PUBLIC"),
    )

    id = models.IntegerField(primary_key=True, auto_created=True, editable=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    title = models.CharField(verbose_name="标题", max_length=30)
    content = models.TextField(verbose_name="正文", )
    created = models.DateField(verbose_name="创建时间", auto_now_add=True)
    status = models.IntegerField(
        verbose_name="状态",
        choices=STATUS_CHOICES,
        default=DRAFT,
    )

    def __str__(self):
        return "<%s @%#x>" % (self.__class__.__name__, id(self))


    class Meta:
        verbose_name_plural = "公告"
        # index_together = ["id", "created"]


class DockerExtra(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    quota = models.IntegerField(verbose_name="允许容器数量", default=1)


class V2rayTemplate(models.Model):
    # TODO: send signal

    CLIENT = "c"
    SERVER = "s"
    STATUS_CHOICES = (
        (CLIENT, "客户端"),
        (SERVER, "服务端"),
    )

    id = models.IntegerField(primary_key=True, auto_created=True, editable=False)
    title = models.CharField(verbose_name="标题", max_length=30)
    type = models.CharField(
        verbose_name="类型",
        max_length=2,
        choices=STATUS_CHOICES,
        default=CLIENT,
    )
    content = models.TextField(verbose_name="配置", default="{}")
    created = models.DateField(verbose_name="创建时间", auto_now_add=True)
    used = models.BooleanField(verbose_name="是否启用", default=False)

    @classmethod
    def from_db(cls, db, field_names, values):
        if len(values) != len(cls._meta.concrete_fields):
            values = list(values)
            values.reverse()
            values = [
                values.pop() if f.attname in field_names else DEFERRED
                for f in cls._meta.concrete_fields
            ]
        instance = cls(*values)
        instance._state.adding = False
        instance._state.db = db
        # customization to store the original field values on the instance
        # instance.content = json.loads(instance.content)
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    def save(self, *args, **kwargs):
        data = self.content
        # data = data.replace("\'", "\"")

        data_dict = json.loads(data)
        self.content = json.dumps(data_dict)

        super(V2rayTemplate, self).save(*args, **kwargs)


    class Meta:
        verbose_name_plural = "V2ray Config"
