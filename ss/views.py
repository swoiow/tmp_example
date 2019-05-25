#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt
import json
from os import environ

import docker
import simplejson as js
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import View

from .docker_utils import Web2DockerMiddleWare as SocksProxy, get_docker_client, run_ss_server
from .models import Billboard, V2rayTemplate
from .v2ray_utils import Web2DockerMiddleWare as V2rayProxy


@login_required(login_url="/adm/login")
def show_billboard(request, post_id):
    post = Billboard.objects.get(pk=post_id)
    # post_content = post.content.replace("\r", "\n")
    return render(request, "ss/billboard.html", context=dict(post=post))


class API(View):

    @staticmethod
    def get_user_info(request, *args, **kwargs):
        user = request.user
        super_admin = user.is_superuser
        username = user.username

        socks_proxy = SocksProxy(username)
        v2ray_proxy = V2rayProxy(username)

        socks_user_info = socks_proxy.get_all_containers() if super_admin else socks_proxy.get_user_containers()
        __map_func__ = map(lambda d: d.update({"type": "ss"}), socks_user_info)
        __call_map_func__ = list(__map_func__)

        v2ray_user_info = v2ray_proxy.info
        if v2ray_user_info:
            v2ray_user_info = API._cover_v2ray_style_to_socks_style(v2ray_user_info)
            v2ray_user_info.update({"type": "v2ray"})

            socks_user_info.insert(0, v2ray_user_info)

        return JsonResponse(dict(rv=socks_user_info))

    @staticmethod
    def get_billboard_info(*args, **kwargs):
        posts = Billboard.objects \
            .filter(status=Billboard.PUBLIC) \
            .order_by("-created")

        return list(posts.values())

    @staticmethod
    def _cover_v2ray_style_to_socks_style(data: dict):
        meta = data["_metadata"]
        meta = meta.replace("\'", "\"")
        meta = json.loads(meta)

        mapping = dict(pwd="id", method="alterId", user="usr", create="ct")
        get_value = lambda k: data.get(mapping[k], meta.get(mapping[k]))
        return {k: get_value(k) for k in mapping.keys()}


class V2rayAdm(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = request.user
        username = user.username
        o = V2rayProxy(username)

        return JsonResponse(dict(result=o.info))

    def put(self, request, *args, **kwargs):
        user = request.user
        username = user.username
        o = V2rayProxy(username)

        st, r = o.create()
        if st:
            self.restart_container(request)
        request.session["msg_box"] = "创建结果: %s" % (st and "创建" or "已存在")

        response = HttpResponse()
        response["Location1"] = "/c/ss"
        return response

    def delete(self, request, *args, **kwargs):
        user = request.user
        username = user.username
        o = V2rayProxy(username)

        r = o.remove_record()
        if r:
            self.restart_container(request)

        request.session["msg_box"] = "删除结果: %s" % r

        response = HttpResponse()
        response["Location1"] = "/c/ss"
        return response

    @staticmethod
    def restart_container(request, *args, **kwargs):
        user = request.user
        username = user.username

        try:
            default_config = V2rayTemplate.objects \
                .filter(used=True) \
                .filter(type=V2rayTemplate.SERVER) \
                .order_by("-created") \
                .latest("id")
        except IndexError:
            return JsonResponse({"result", "IndexError"})

        o = V2rayProxy(username)
        r = o.restart(confg_template=default_config.content)

        request.session["msg_box"] = "重启结果: %s" % r

        response = HttpResponse()
        response["Location1"] = "/c/ss"
        return response


class SSAdm(LoginRequiredMixin, View):
    login_url = "/adm/login?next=/c/ss"

    def get(self, request, *args, **kwargs):
        user = request.user
        super_admin = user.is_superuser
        username = user.username

        ctx = {
            "IP": environ.get("SERVER_IP", "127.0.0.1"),
            "user": {
                "name": username,
                "is_admin": super_admin,
            },
            # "ds": js.dumps(data),
            "billboard": API.get_billboard_info(),
            "message": "msg_box" in request.session and request.session.pop("msg_box")
        }

        return render(request, "ss/index.html", context=ctx)

    def post(self, request, *args, **kwargs):
        fetch_request = json.loads(request.body.decode())
        user = request.user
        super_admin = user.is_superuser
        username = user.username

        o = SocksProxy(username)

        if fetch_request.get("action") == "invite" and super_admin:
            import uuid
            from redis import StrictRedis

            info = environ["REDIS"].split(":")
            _host = info[0]
            _port = info[1] if len(info) > 1 else 6379
            rds = StrictRedis(host=_host, port=_port, db=1, socket_keepalive=10, socket_connect_timeout=10)

            usr_id = str(uuid.uuid4())
            rds.set(usr_id, value=js.dumps({"email": fetch_request["email"]}), ex=3 * 24 * 60 * 60)

            request.session["msg_box"] = "记录成功: %s" % usr_id

        elif fetch_request.get("action") == "transfer" and super_admin:
            resp = o.transfer_container(fetch_request["usr"], fetch_request["id"])

            if resp:
                request.session["msg_box"] = "转移成功"
            else:
                request.session["msg_box"] = "转移失败: 权限不够或用户(容器)不存在"

        elif fetch_request.get("action") == "restore":
            c_id = fetch_request["id"]

            if super_admin:
                o.get_all_containers()

                # patch user
                real_user = json.loads(o.mapping[c_id])["user"]
                o = SocksProxy(real_user)

            lost_container = [i for i in o.get_user_containers() if i["container_id"] == c_id][0]
            response = run_ss_server(username, pwd=lost_container["pwd"], port=lost_container["port"])

            if response:
                lost_container["container_id"] = response.short_id
                lost_container["create"] = dt.datetime.today().strftime("%Y-%m-%d")

                o.add_container(lost_container)
                o.remove_container_record(c_id)
                request.session["msg_box"] = "还原成功"

        elif fetch_request.get("action") == "new" and (o.length < user.dockerextra.quota or super_admin):
            kw = {}
            if fetch_request.get("enc"):
                kw["enc_mode"] = fetch_request["enc"]
            response = run_ss_server(username, **kw)

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
                request.session["msg_box"] = "创建成功"

            else:
                request.session["msg_box"] = "创建失败，请尝试删除所有容器"

        else:
            request.session["msg_box"] = "超出配额数量, 或指令不被接受"

        response = HttpResponse()
        response["Location1"] = "/c/ss"
        return response

    def put(self, request, *args, **kwargs):
        user = request.user
        username = user.username

        client = get_docker_client()
        o = SocksProxy(username)

        for record in o.get_user_containers():
            try:
                container = client.containers.get(record["container_id"])
                container.stop()

            except docker.errors.NotFound:
                pass

        o.user_rest_all()

        request.session["msg_box"] = "当前用户已清空"

        response = HttpResponse()
        response["Location1"] = "/c/ss"
        return response

    def delete(self, request, *args, **kwargs):
        user = request.user
        super_admin = user.is_superuser
        username = user.username

        if request.body:
            cid = json.loads(request.body.decode())["id"]
            o = SocksProxy(username)

            if super_admin:
                o.get_all_containers()

                # patch user
                real_user = json.loads(o.mapping[cid])["user"]
                o = SocksProxy(real_user)

            if o.has_container(cid):
                try:
                    client = get_docker_client()

                    container = client.containers.get(cid)
                    container.stop()

                    request.session["msg_box"] = "已删除"
                    o.remove_container_record(cid)

                except docker.errors.NotFound:
                    request.session["msg_box"] = "容器不存在或已删除"

        response = HttpResponse()
        response["Location1"] = "/c/ss"
        return response
