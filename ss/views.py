#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt
import json as js
from os import environ

import docker
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View

from .docker_utils import Web2DockerMiddleWare, run_ss_server


class SSAdm(LoginRequiredMixin, View):
    login_url = "/adm/login?next=/ss/"

    def get(self, request, *args, **kwargs):
        user = request.user
        username = user.username

        o = Web2DockerMiddleWare(username)
        if user.is_superuser:
            data = o.get_all_containers()
        else:
            data = o.get_user_containers()

        ctx = {
            "IP": environ.get("server_ip", "127.0.0.1"),
            "user": username,
            "ds": js.dumps(data),
            "message": "msg_box" in request.session and request.session.pop("msg_box")
        }

        return render(request, "ss/index.html", context=ctx)

    def post(self, request, *args, **kwargs):
        fetch_request = js.loads(request.body.decode())
        user = request.user
        username = user.username

        o = Web2DockerMiddleWare(username)

        if fetch_request.get("action") == "transfer" and user.is_superuser:
            resp = o.transfer_container(fetch_request["usr"], fetch_request["id"])

            if resp:
                request.session['msg_box'] = "转移成功"
            else:
                request.session['msg_box'] = "转移失败: 权限不够或用户(容器)不存在"

        elif fetch_request.get("action") == "new" and (o.length < 2 or user.is_superuser):
            response = run_ss_server(username)

            if response:
                td = dt.datetime.today().strftime("%Y-%m-%d")
                data = dict(
                    container_id=response.short_id,
                    user=username,
                    create=dt.datetime.today().strftime("%Y-%m-%d"),
                    pwd=response.ext.pwd,
                    method=response.ext.enc_mode,
                    port=response.ext.port,
                    more_sec=0,
                    note=fetch_request.get("note", "%s-%s" % (username, td)),
                )

                o.add_container(data)
                request.session['msg_box'] = "创建成功"

            else:
                request.session['msg_box'] = "创建失败，请尝试删除所有容器"

        else:
            request.session['msg_box'] = "未知指令或超出创建数量限制"

        response = HttpResponse()
        response["Location1"] = "/ss"
        return response

    def put(self, request, *args, **kwargs):
        user = request.user
        username = user.username

        client = docker.APIClient(base_url=environ["DOCKER_SOCK"])
        o = Web2DockerMiddleWare(username)

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

        o = Web2DockerMiddleWare(username)

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
