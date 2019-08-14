#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import AnyStr

from django.contrib.auth.models import User

from adm.apps import AdmConfig
from vendor.redis import RedisPlus
from vendor.utils import js


def create_user(
        username,
        password,
        email,
):
    return User.objects.create_user(
        username=username,
        password=password,
        email=email,
        is_staff=True
    ).save()


def save_invite_data(uuid: AnyStr, **kwargs):
    rds = RedisPlus(db_space=AdmConfig.redis_db_space)
    rds.set(uuid, **kwargs)


def load_invite_data(uuid: AnyStr):
    rds = RedisPlus(db_space=AdmConfig.redis_db_space)

    try:
        return js.to_json(rds.get(uuid))
    except TypeError:
        return


def delete_invite_data(username: AnyStr, uuid: AnyStr):
    rds = RedisPlus(db_space=AdmConfig.redis_db_space)
    if User.objects.filter(username=username).count() >= 1:
        rds.delete(uuid)
