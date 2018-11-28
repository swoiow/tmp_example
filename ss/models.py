#!/usr/bin/env python
# -*- coding: utf-8 -*

import uuid

from django.contrib.auth.models import User
from django.db import models


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
