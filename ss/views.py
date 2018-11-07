#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt
import json as js
import random
import string
from os import environ

import docker
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View
from redis import StrictRedis


def random_password(size=(10, 16)):
    seeds = string.ascii_uppercase + string.ascii_lowercase + string.digits
    size = random.randint(*size)
    return "".join(random.choice(seeds) for x in range(size))


def random_port():
    return random.randint(10000, 63300)


def helper(request):
    return render(request, "ss/help.html")


def run_ss_server(name, pwd=None, port=None, enc_mode="aes-128-cfb"):
    client = docker.DockerClient(base_url=environ["DOCKER_SOCK"])

    if not pwd:
        pwd = random_password()
        # print(pwd)

    if not port:
        rport = random_port()
        # print(rport)
    else:
        rport = port

    container_port = random_port()
    extra = "--fast-open --reuse-port -t 300 -6"

    img_name = "pylab/shadowsocks:latest"
    command = "ss-server -s 0.0.0.0 -p {lport} -k {pwd} -m {enc_mode} {extra}"

    try:
        response = client.containers.run(
            image=img_name,
            command=command.format(pwd=pwd, lport=container_port, enc_mode=enc_mode, extra=extra),

            detach=True,
            # name="ss_%s" % name,
            auto_remove=True,
            remove=True,
            network_mode="bridge",
            ports={
                "%s/tcp" % container_port: rport,
                # "%s/udp" % container_port: rport,
            },
            ulimits=[
                {"name": "nofile", "soft": 20000, "hard": 40000},
                {"name": "nproc", "soft": 65535, "hard": 65535},
            ]
        )

        return pwd, rport, enc_mode, response

    except docker.errors.APIError:
        return False, False, False, False


def proxy(request):
    return render(request, "ss/proxy.html")


class Stored(object):
    def __init__(self, user):
        self.user = user
        self.rds = StrictRedis(host=environ["REDIS"], socket_keepalive=10)
        self._mapping = {}

    @property
    def mapping(self):
        return self._mapping

    def get_all_containers(self):
        keys = self.rds.keys()
        json_data = []

        for user in keys:
            data = self.rds.smembers(user)

            for idx, r in enumerate(data):
                o = js.loads(r)
                json_data.append(o)

        return json_data

    def get_user_containers(self):
        self._mapping.clear()

        json_data = []
        data = self.rds.smembers(self.user)

        for idx, r in enumerate(data):
            o = js.loads(r)
            self._mapping[o["container_id"]] = r
            json_data.append(o)

        return json_data

    def add_container(self, data):
        self.rds.sadd(self.user, js.dumps(data))
        return True

    def get_exist_length(self):
        return self.rds.scard(self.user)

    def has_container(self, cid):
        for i in self.get_user_containers():
            if cid == i["container_id"]:
                return True

    def remove_container_record(self, cid):
        for i in self.get_user_containers():
            if cid == i["container_id"]:
                return self.rds.srem(self.user, self.mapping[cid])

    def command(self, command, params):
        c = self.rds.__getattribute__(command)
        c(params)


class SSAdm(LoginRequiredMixin, View):
    login_url = "/adm/login?next=/ss/"

    def get(self, request, *args, **kwargs):
        user = request.user
        username = user.username

        o = Stored(username)
        if user.is_superuser:
            data = o.get_all_containers()
        else:
            data = o.get_user_containers()

        ctx = {
            "user": username,
            "ds": js.dumps(data),
            "message": "msg_box" in request.session and request.session.pop("msg_box")
        }

        return render(request, "ss/index.html", context=ctx)

    def post(self, request, *args, **kwargs):
        user = request.user
        username = user.username

        o = Stored(username)

        if o.get_exist_length() < 2 or user.is_superuser:
            pwd, port, enc_mode, response = run_ss_server(username)

            if response:
                data = dict(
                    container_id=response.short_id,
                    user=username,
                    create=dt.datetime.today().strftime("%Y-%m-%d"),
                    pwd=pwd,
                    method=enc_mode,
                    port=port,
                    more_sec=0,
                    note=js.loads(request.body.decode()).get("note"),
                )

                o.add_container(data)

            else:
                request.session['msg_box'] = "创建失败，请尝试删除所有容器"

        else:
            request.session['msg_box'] = "超出数量限制了"

        response = HttpResponse()
        response["Location1"] = "/ss"
        return response

    def put(self, request, *args, **kwargs):

        user = request.user
        username = user.username

        client = docker.APIClient(base_url=environ["DOCKER_SOCK"])
        o = Stored(username)

        try:
            client.stop("ss_%s" % username)

        except docker.errors.NotFound:
            pass

        for container in o.get_user_containers():
            try:
                client.stop(container["container_id"])

            except docker.errors.NotFound:
                pass

        o.command("delete", username)

        request.session['msg_box'] = "当前用户已清空"

        response = HttpResponse()
        response["Location1"] = "/ss"
        return response

    def delete(self, request, *args, **kwargs):

        user = request.user
        username = user.username

        o = Stored(username)

        if request.body:
            cid = js.loads(request.body.decode())["id"]

            if o.has_container(cid):
                try:
                    client = docker.APIClient(base_url=environ["DOCKER_SOCK"])
                    client.stop(cid)

                    request.session['msg_box'] = "已删除"

                except docker.errors.NotFound:
                    request.session['msg_box'] = "容器不存在或已删除"

                o.remove_container_record(cid)

        response = HttpResponse()
        response["Location1"] = "/ss"
        return response
