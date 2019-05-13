#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import environ

from django.apps import AppConfig
from django.db.models.signals import post_save


__redis_info__ = environ["REDIS"].split(":")


class SsConfig(AppConfig):
    name = 'ss'

    rds_host = __redis_info__[0]
    rds_port = __redis_info__[1] if len(__redis_info__) > 1 else 6379

    def ready(self):
        from . import signals

        post_save.connect(signals.init_extra, sender=self)
