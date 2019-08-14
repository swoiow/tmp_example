#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import models


def init_docker_extra_for_new_user(user):
    docker_extra = models.DockerExtra(user=user, quota=1)
    docker_extra.save()
