#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models


@receiver(post_save, sender=User)
def init_extra(sender, *args, **kwargs):
    user = kwargs["instance"]

    if kwargs["created"]:
        docker_extra = models.DockerExtra(user=user)
        docker_extra.save()
