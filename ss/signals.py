#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import services


@receiver(post_save, sender=User)
def init_extra(sender, *args, **kwargs):
    user = kwargs["instance"]

    if kwargs["created"]:
        services.init_docker_extra_for_new_user(user)
