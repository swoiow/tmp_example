#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.apps import AppConfig
from django.db.models.signals import post_save


class SsConfig(AppConfig):
    name = 'ss'

    redis_db_space = 1

    def ready(self):
        from . import signals

        post_save.connect(signals.init_extra, sender=self)
