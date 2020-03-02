#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.apps import AppConfig
from django.db.models.signals import post_save


class Config(AppConfig):
    name = 'ftw'

    redis_db_space = 1

    def ready(self):
        from . import signals

        post_save.connect(signals.init_extra, sender=self)


DNS = ["1.1.1.1", "1.0.0.1", "208.67.222.222", "8.8.8.8", "2606:4700:4700::1111"]
ULIMITS_SOFT = 50000 * 2
ULIMITS_HARD = 51200 * 2

DEFAULT_SS_IMAGE = "pylab/net:latest"
DEFAULT_V2RAY_CONTAINER_NAME = "web2net"
