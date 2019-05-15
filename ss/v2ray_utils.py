#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt
import json
import random
import traceback
import uuid
from os import environ, path
from typing import Dict, List

import docker
import simplejson as js
from redis import StrictRedis

from .docker_utils import get_docker_client


config_path = environ.get("CONFIG_SERVER", "config-server.json")

if path.isfile(config_path):
    with open(config_path, "rb") as rf:
        server_config = json.load(rf)


def generate_user(usr: str) -> Dict:
    data = {
        "id": str(uuid.uuid4()),
        "alterId": random.randint(4, 64),
        "_metadata": {
            "usr": usr,
            "ct": dt.datetime.today().isoformat()
        }
    }
    return data


def update_config(config: Dict, users: List[Dict]) -> Dict:
    inbounds = config["inbounds"]
    for items in inbounds:
        clients = items["settings"]["clients"]

        clients.extend(users)
        items["settings"]["clients"] = clients

    return config


class Web2DockerMiddleWare(object):

    def __init__(self, user):
        info = environ["REDIS"].split(":")
        _host = info[0]
        _port = info[1] if len(info) > 1 else 6379

        self.user = user
        self.redis_key = f"v2ray|{self.user}"

        self.rds = StrictRedis(
            host=_host, port=_port, socket_keepalive=10,
            charset="utf-8", decode_responses=True
        )

    @property
    def info(self):
        return self.rds.hgetall(f"{self.redis_key}")

    def create(self):
        if self.user and not self.rds.get(self.redis_key):
            self.rds.hmset(self.redis_key, generate_user(self.user))
            return True
        return False

    def remove_record(self):
        return self.rds.delete(self.redis_key) and True or False

    @staticmethod
    def stop_container(**kwargs):
        client = get_docker_client()

        try:
            container = client.containers.get("v2ray")
            container.stop()
            return True

        except docker.errors.NotFound:
            pass

    def start_container(self, **kwargs):
        """
            https://github.com/docker/machine/issues/4235
            https://github.com/v2ray/discussion/issues/11

            echo '{"inbounds": [{"port": 12345, "protocol": "vmess", "settings": {"clients": []}, "streamSettings": {"network": "ws", "wsSettings": {"path": "/service-path/"}}}], "outbounds": [{"protocol": "freedom", "settings": {}}]}' |  dk run -i  v2ray  v2ray  -config=stdin: cat -
        """

        config = kwargs.get("confg_template")
        if not config:
            return False

        config = update_config(config, list(self._get_all_users()))
        config = js.dumps(config)
        command = f'v2ray -config=stdin: <<< {config}'
        client = get_docker_client()

        try:
            client.containers.run(
                image="v2ray",
                name="v2ray",
                command=command,
                user="nobody",
                detach=True,
                auto_remove=True,
                remove=True,
                ports={
                    "8388/tcp": 1090,
                    "8388/udp": 1090,
                },
                dns_opt=["1.1.1.1", "8.8.8.8"],
                stdin_open=True,
                # tty=True,  # this param is for stdin
                ulimits=[
                    {
                        "name": "nofile",
                        "soft": 20000,
                        "hard": 40000
                    },
                    {
                        "name": "nproc",
                        "soft": 65535,
                        "hard": 65535
                    },
                ],
                labels={
                    "owner": "system",
                    "created": dt.datetime.today().strftime("%Y-%m-%d")
                },
            )

            return True

        except docker.errors.APIError:
            traceback.print_exc()
            return False

    def restart(self, **kwargs):
        self.stop_container(**kwargs)
        return self.start_container(**kwargs)



    def _get_all_users(self):
        for user_key in self.rds.scan_iter("v2ray|*"):
            user_json = self.rds.hgetall(user_key)
            yield user_json
