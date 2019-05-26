#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt
import json
import random
import string
import traceback
from os import environ
from typing import Dict, List

import docker
import simplejson as js
from redis import StrictRedis


def get_docker_client() -> docker.client:
    if "DOCKER_SOCK" in environ:
        client = docker.DockerClient(base_url=environ["DOCKER_SOCK"])
    else:
        client = docker.from_env()

    return client


def random_seed(size=(20, 32)):
    seeds = string.ascii_uppercase + string.ascii_lowercase + string.digits
    size = random.randint(*size)
    return "".join(random.choice(seeds) for x in range(size))


def random_port():
    return random.randint(30000, 63300)


def run_ss_server(name, pwd=None, port=None, enc_mode="aes-128-gcm", img=None):
    client = get_docker_client()
    if not img:
        img = environ.get("SS_IMG", "pylab/shadowsocks-libev:latest")

    if not pwd:
        pwd = random_seed()
        # print(pwd)

    if not port:
        rport = random_port()
        # print(rport)
    else:
        rport = port

    container_port = random_port()
    extra = "-u --fast-open --reuse-port -t 80"

    img_name = img
    command = f"ss-server -s 0.0.0.0 -p {container_port} -k {pwd} -m {enc_mode} {extra}"

    try:
        client.images.pull(img_name)
        response = client.containers.run(
            image=img_name,
            name="ss_%s_%s" % (name, random_seed(size=(2, 4))),
            command=command,
            user="nobody",
            detach=True,
            auto_remove=True,
            remove=True,
            ports={
                "%s/tcp" % container_port: rport,
                "%s/udp" % container_port: rport,
            },
            dns_opt=["1.1.1.1", "8.8.8.8"],
            ulimits=[{
                "name": "nofile",
                "soft": 20000,
                "hard": 40000,
            }, {
                "name": "nproc",
                "soft": 65535,
                "hard": 65535,
            }],
            labels={
                "owner": name,
                "created": dt.datetime.today().strftime("%Y-%m-%d")
            },
        )

        ext = type("EXT", (object,), {})()
        ext.pwd = pwd
        ext.port = rport
        ext.enc_mode = enc_mode

        response.ext = ext

        return response

    except docker.errors.APIError:
        traceback.print_exc()
        return False


class Web2DockerMiddleWare(object):
    _rds_flag = "socks|"

    def __init__(self, user):
        info = environ["REDIS"].split(":")
        _host = info[0]
        _port = info[1] if len(info) > 1 else 6379

        self.user = user
        self.usr_rds_key = f"{self._rds_flag}{self.user}"
        self.rds = StrictRedis(host=_host, port=_port, socket_keepalive=10)
        self._mapping = {}  # {'cid': json.dumps()}

    @property
    def mapping(self) -> Dict:
        return self._mapping

    @property
    def length(self):
        return self.rds.scard(self.user)

    def get_all_containers(self) -> List:
        keys = self.rds.keys(f"{self._rds_flag}*")
        json_data = []

        for user in keys:
            data = self.rds.smembers(user)

            for idx, r in enumerate(data):
                o = json.loads(r)
                self._mapping[o["container_id"]] = r
                json_data.append(o)

        return json_data

    def get_user_containers(self) -> List:
        self._mapping.clear()

        json_data = []
        data = self.rds.smembers(self.usr_rds_key)

        for idx, r in enumerate(data):
            o = json.loads(r)
            self._mapping[o["container_id"]] = r
            json_data.append(o)

        return json_data

    def add_container(self, data, usr_key=None):
        if not usr_key:
            usr_key = self.usr_rds_key

        self.rds.sadd(usr_key, js.dumps(data))
        return True

    def has_container(self, cid):
        for i in self.get_user_containers():
            if cid == i["container_id"]:
                return True

    def remove_container_record(self, cid):
        for i in self.get_user_containers():
            if cid == i["container_id"]:
                return self.rds.srem(self.usr_rds_key, self.mapping[cid])

    def transfer_container(self, usr, cid):
        for i in self.get_user_containers():
            if cid == i["container_id"]:
                data = json.loads(self.mapping[cid])
                data["user"] = usr
                data["note"] = "transfer from %s" % self.user

                self.add_container(data, usr_key=f"{self._rds_flag}{usr}")
                self.remove_container_record(cid)

                return True

        return False

    def user_rest_all(self):
        self._command("delete", self.usr_rds_key)

    def _command(self, command, params):
        c = self.rds.__getattribute__(command)
        c(params)
