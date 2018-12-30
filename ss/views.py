#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt
import json as js
from os import environ

import docker
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View

from .docker_utils import Web2DockerMiddleWare, get_docker_client, run_ss_server
from .models import Billboard


@login_required
def show_billboard(request, post_id):
    post = Billboard.objects.get(pk=post_id)
    # post_content = post.content.replace("\r", "\n")
    return render(request, "ss/billboard.html", context=dict(post=post))


class SSAdm(LoginRequiredMixin, View):
    login_url = "/adm/login?next=/ss/"

    def get(self, request, *args, **kwargs):
        user = request.user
        super_admin = user.is_superuser
        username = user.username

        o = Web2DockerMiddleWare(username)
        if super_admin:
            data = o.get_all_containers()
        else:
            data = o.get_user_containers()

        posts = Billboard.objects \
            .filter(status=Billboard.PUBLIC) \
            .order_by("-created")

        ctx = {
            "IP": environ.get("SERVER_IP", "127.0.0.1"),
            "user": {
                "name": username,
                "is_admin": super_admin,
            },
            "ds": js.dumps(data),
            "billboard": list(posts.values()),
            "message": "msg_box" in request.session and request.session.pop("msg_box")
        }

        return render(request, "ss/index.html", context=ctx)

    def post(self, request, *args, **kwargs):
        fetch_request = js.loads(request.body.decode())
        user = request.user
        super_admin = user.is_superuser
        username = user.username

        o = Web2DockerMiddleWare(username)

        if fetch_request.get("action") == "invite" and super_admin:
            import uuid
            from redis import StrictRedis

            info = environ["REDIS"].split(":")
            _host = info[0]
            _port = info[1] if len(info) > 1 else 6379
            rds = StrictRedis(host=_host, port=_port, db=1, socket_keepalive=10, socket_connect_timeout=10)

            usr_id = str(uuid.uuid4())
            rds.set(usr_id, value=js.dumps({"email": fetch_request["email"]}), ex=3 * 24 * 60 * 60)

            request.session['msg_box'] = "记录成功: %s" % usr_id

        elif fetch_request.get("action") == "transfer" and super_admin:
            resp = o.transfer_container(fetch_request["usr"], fetch_request["id"])

            if resp:
                request.session['msg_box'] = "转移成功"
            else:
                request.session['msg_box'] = "转移失败: 权限不够或用户(容器)不存在"

        elif fetch_request.get("action") == "new" and (o.length < user.dockerextra.quota or super_admin):
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
            request.session['msg_box'] = "超出配额数量, 或指令不被接受"

        response = HttpResponse()
        response["Location1"] = "/ss"
        return response

    def put(self, request, *args, **kwargs):
        user = request.user
        username = user.username

        client = get_docker_client()
        o = Web2DockerMiddleWare(username)

        for record in o.get_user_containers():
            try:
                container = client.containers.get(record["container_id"])
                container.stop()

            except docker.errors.NotFound:
                pass

        o.command("delete", username)

        request.session['msg_box'] = "当前用户已清空"

        response = HttpResponse()
        response["Location1"] = "/ss"
        return response

    def delete(self, request, *args, **kwargs):
        user = request.user
        super_admin = user.is_superuser
        username = user.username

        if request.body:
            cid = js.loads(request.body.decode())["id"]
            o = Web2DockerMiddleWare(username)

            if super_admin:
                o.get_all_containers()

                # patch user
                real_user = js.loads(o.mapping[cid])["user"]
                o = Web2DockerMiddleWare(real_user)

            if o.has_container(cid):
                try:
                    client = get_docker_client()

                    container = client.containers.get(cid)
                    container.stop()

                    request.session['msg_box'] = "已删除"
                    o.remove_container_record(cid)

                except docker.errors.NotFound:
                    request.session['msg_box'] = "容器不存在或已删除"

        response = HttpResponse()
        response["Location1"] = "/ss"
        return response
