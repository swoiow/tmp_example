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

from ss.utils.shadowsocks import get_docker_client
from .w2d import Web2Docker


config_path = environ.get("CONFIG_SERVER", "config-server.json")

if path.isfile(config_path):
    with open(config_path, "rb") as rf:
        server_config = json.load(rf)


def generate_user(usr: str) -> Dict:
    data = {
        "id": str(uuid.uuid4()),
        "alterId": random.randint(4, 32),
        "_metadata": {
            "usr": usr,
            "ct": dt.datetime.today().strftime("%Y-%m-%d")
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


class Web2DockerMiddleWare(Web2Docker):
    _rds_flag = "v2ray|"
    _container_name = "django-v2ray"

    def __init__(self, user):
        info = environ["REDIS"].split(":")
        _host = info[0]
        _port = info[1] if len(info) > 1 else 6379

        self.user = user
        self.usr_rds_key = f"{self._rds_flag}{self.user}"

        self.rds = StrictRedis(host=_host, port=_port, socket_keepalive=10, charset="utf-8", decode_responses=True, )

    @property
    def info(self):
        rds_data = self.rds.get(f"{self.usr_rds_key}")
        return self.from_json(rds_data)

    def create(self):
        user_data = self.rds.get(self.usr_rds_key)
        if user_data:
            return False, user_data

        user_data = generate_user(self.user)
        rds_user_data = self.to_json(user_data)
        self.rds.set(self.usr_rds_key, rds_user_data)

        return True, user_data

    def remove_record(self, username=None):
        usr_rds_key = username and f"{self._rds_flag}{username}" or self.usr_rds_key
        return self.rds.delete(usr_rds_key) and True or False

    def remove_container(self, **kwargs):
        client = get_docker_client()

        try:
            container = client.containers.get(self._container_name)
            container.remove()
            return True

        except docker.errors.NotFound:
            return False

    def stop_container(self, **kwargs):
        client = get_docker_client()

        try:
            container = client.containers.get(self._container_name)
            container.stop()
            return True

        except docker.errors.NotFound:
            return False

    def start_container(self, **kwargs):
        """
            https://github.com/docker/machine/issues/4235
            https://github.com/v2ray/discussion/issues/11

            echo '{"inbounds": [{"port": 12345, "protocol": "vmess", "settings": {"clients": []}, "streamSettings": {"network": "ws", "wsSettings": {"path": "/service-path/"}}}], "outbounds": [{"protocol": "freedom", "settings": {}}]}' |  dk run -i  v2ray  v2ray  -config=stdin: cat -
            docker run -i v2ray v2ray -test -config=stdin: <<< '{"inbounds": [{"port": 12345, "protocol": "vmess", "settings": {"clients": []}, "streamSettings": {"network": "ws", "wsSettings": {"path": "/service-path/"}}}], "outbounds": [{"protocol": "freedom", "settings": {}}]}'
        """

        config = kwargs.get("confg_template")
        if not config:
            return "服务端模板没定义或没开启"
        config = json.loads(config)

        users_data = list(self._get_all_users())
        if not users_data:
            return "没有任何的用户数据，中止创建"

        config = update_config(config, users_data)
        str_config = js.dumps(config, separators=(",", ":"))
        double_encode = js.dumps(str_config)

        command = f"v2ray -test -config=stdin: <<< '{str_config}'"
        client = get_docker_client()

        try:
            client.containers.run(
                image="pylab/v2ray",
                name=self._container_name,
                command=command,
                user="nobody",
                detach=True,
                # auto_remove=True,
                # remove=True,
                ports={
                    "1090/tcp": ("0.0.0.0", 1090),
                    "1090/udp": ("0.0.0.0", 1090),
                },
                dns_opt=["1.1.1.1", "8.8.8.8"],
                stdin_open=True,
                # tty=True,  # this param is for stdin
                ulimits=[{
                    "name": "nofile",
                    "soft": 20000,
                    "hard": 40000
                }, {
                    "name": "nproc",
                    "soft": 65535,
                    "hard": 65535
                }],
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
        self.remove_container(**kwargs)
        return self.start_container(**kwargs)

    def _get_all_users(self):
        for user_key in self.rds.scan_iter(f"{self._rds_flag}*"):
            rds_data = self.rds.get(user_key)
            rds_data = self.from_json(rds_data)
            yield rds_data
