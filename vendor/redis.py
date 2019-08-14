#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings
from os import environ

import redis

__all__ = ["RedisPlus"]

pool = {}


def redis_inst(db_space: int = 0, **kwargs) -> redis.StrictRedis:
    rds_host = environ.get("REDIS_HOST")
    rds_port = environ.get("REDIS_PORT", 6379)

    if db_space in pool:
        return pool[db_space]

    if not rds_host:
        warnings.warn(("redis is unset in env.",))

        import fakeredis
        server = fakeredis.FakeServer()
        rds = fakeredis.FakeStrictRedis(
            server=server,
            port=rds_port,
            db=db_space,
            **kwargs
        )

        warnings.warn(("use fakeredis lib.",))

    else:
        rds = redis.StrictRedis(
            host=rds_host,
            port=rds_port,
            socket_keepalive=300,
            db=db_space,
            **kwargs
        )

    pool[db_space] = rds

    return redis_inst(db_space=db_space)


RedisPlus = redis_inst
