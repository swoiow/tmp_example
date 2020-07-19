#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json as sys_json
from os import environ
from typing import AnyStr, Dict

import docker
import ujson as sdt_json


def load_json(data: AnyStr = None, fp=None, *args, **kwargs):
    if fp: return sys_json.load(fp, *args, **kwargs)

    return sys_json.loads(data, *args, **kwargs)


def dump_json(obj: Dict, fp=None, *args, **kwargs):
    if fp: return sdt_json.dump(obj, fp, *args, **kwargs)

    return sdt_json.dumps(obj, *args, **kwargs)


class _Json(object):
    to_json = staticmethod(load_json)
    from_str = staticmethod(load_json)
    load_json = staticmethod(load_json)

    to_str = staticmethod(dump_json)
    from_json = staticmethod(dump_json)
    dump_json = staticmethod(dump_json)


js = _Json()


def get_docker_client() -> docker.client:
    if "DOCKER_SOCK" in environ:
        client = docker.DockerClient(base_url=environ["DOCKER_SOCK"])
    else:
        client = docker.from_env()

    return client
