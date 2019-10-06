#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt
from os import environ

import docker
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

import adm.services as adm_service
from ss.utils import SocksVendor, V2rayVendor
from ss.utils.schema import SockSchema, V2raySchema
from ss.utils.shadowsocks import run_ss_server
from ss.utils.views import LoginRequiredMixin
from vendor.redis import RedisPlus
from vendor.utils import js, get_docker_client
from .models import Billboard, V2rayTemplate


@login_required(login_url="/adm/login")
def show_billboard(request, post_id):
    post = Billboard.objects.get(pk=post_id)
    return render(request, "ss/billboard.html", context=dict(post=post))


class V2rayAdm(LoginRequiredMixin):

    def get(self, request, *args, **kwargs):
        user = request.user
        username = user.username
        o = V2rayVendor(username)
        result = o.info
        if result:
            result["security"] = "aes-128-gcm"

            try:
                default_config = V2rayTemplate.objects \
                    .filter(used=True) \
                    .filter(type=V2rayTemplate.CLIENT) \
                    .order_by("-created") \
                    .latest("id")
            except Exception:
                pass
            else:
                result = default_config.content.replace('"@USER@"', js.to_str(result))
                result = js.from_str(result)

        result_in_str = js.to_str(result, indent=2, sort_keys=True)
        if "as_file" in request.GET:
            response = HttpResponse(result_in_str, content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="config.json"'
        else:
            response = HttpResponse(result_in_str, content_type="application/json")

        return response

    def put(self, req, *args, **kwargs):
        user = req.user
        username = user.username
        o = V2rayVendor(username)

        result, data = o.create()
        if result:
            self.restart_container(req)

        self.set_message(req, "创建结果: %s" % (result and "已成功" or "已存在"))

        resp = HttpResponse()
        resp["Location1"] = "/c/ss"
        return resp

    def delete(self, req, *args, **kwargs):
        user = req.user
        username = user.username
        super_admin = user.is_superuser

        o = V2rayVendor(username)
        if req.body:
            usr = js.load_json(req.body.decode())["user"]

            if super_admin:
                o = V2rayVendor(usr)

        result = o.remove_record()
        if result:
            self.restart_container(req)

        self.set_message(req, f"删除结果: {result}")

        resp = HttpResponse()
        resp["Location1"] = "/c/ss"
        return resp

    @staticmethod
    def restart_container(req, *args, **kwargs):
        user = req.user
        username = user.username

        try:
            default_config = V2rayTemplate.objects \
                .filter(used=True) \
                .filter(type=V2rayTemplate.SERVER) \
                .order_by("-created") \
                .latest("id")
        except IndexError:
            # return JsonResponse({"result", "IndexError"})
            req.session["msg_box"] = "重启结果: IndexError"

        else:
            o = V2rayVendor(username)
            result = o.restart(confg_template=default_config.content)

            req.session["msg_box"] = f"重启结果: {result}"

        resp = HttpResponse()
        resp["Location"] = "/c/ss"
        return resp


class SSAdm(LoginRequiredMixin):

    def post(self, req, *args, **kwargs):

        fetch_request = js.load_json(req.body.decode())
        user = req.user
        super_admin = user.is_superuser
        username = user.username

        o = SocksVendor(username)

        if fetch_request.get("action") == "invite" and super_admin:
            self.handle_action_invite(req=req, fetch_request=fetch_request)

        elif fetch_request.get("action") == "transfer" and super_admin:
            self.handle_action_transfer(username=username, req=req, fetch_request=fetch_request)

        elif fetch_request.get("action") == "restore":
            self.handle_action_restore(username=username, req=req, fetch_request=fetch_request, super_admin=super_admin)

        elif fetch_request.get("action") == "new" and (o.length < user.dockerextra.quota or super_admin):
            self.handle_action_new(username=username, req=req, fetch_request=fetch_request)

        else:
            self.set_message(req, "超出配额数量, 或指令不被接受")

        resp = HttpResponse()
        resp["Location1"] = "/c/ss"
        return resp

    def put(self, req, *args, **kwargs):
        user = req.user
        username = user.username

        client = get_docker_client()
        o = SocksVendor(username)

        for record in o.get_user_containers():
            try:
                container = client.containers.get(record["container_id"])
                container.stop()

            except docker.errors.NotFound:
                pass

        o.user_rest_all()

        self.set_message(req, "当前用户已清空")

        resp = HttpResponse()
        resp["Location1"] = "/c/ss"
        return resp

    def delete(self, req, *args, **kwargs):
        user = req.user
        super_admin = user.is_superuser
        username = user.username

        if req.body:
            cid = js.load_json(req.body.decode())["id"]
            o = SocksVendor(username)

            if super_admin:
                o.get_all_containers()

                # patch user
                real_user = js.load_json(o.mapping[cid])["user"]
                o = SocksVendor(real_user)

            if o.has_container(cid):
                try:
                    client = get_docker_client()

                    container = client.containers.get(cid)
                    container.stop()

                    self.set_message(req, "已删除")
                    o.remove_container_record(cid)

                except docker.errors.NotFound:
                    self.set_message(req, "容器不存在或已删除")

        resp = HttpResponse()
        resp["Location1"] = "/c/ss"
        return resp

    def handle_action_invite(self, req, fetch_request, *args, **kwargs):
        import uuid
        rds = RedisPlus(db_space=1)

        usr_id = str(uuid.uuid4())
        adm_service.save_invite_data(
            usr_id,
            value=js.to_str({"email": fetch_request["email"]}),
            ex=3 * 24 * 60 * 60,
        )

        self.set_message(req, f"记录成功: {usr_id}")

    def handle_action_transfer(self, username, req, fetch_request, *args, **kwargs):
        o = SocksVendor(username)

        resp = o.transfer_container(fetch_request["usr"], fetch_request["id"])

        if resp:
            self.set_message(req, "转移成功")
        else:
            self.set_message(req, "转移失败: 权限不够或用户(容器)不存在")

    def handle_action_restore(self, username, req, fetch_request, *args, **kwargs):
        o = SocksVendor(username)

        c_id = fetch_request["id"]

        if kwargs["super_admin"]:
            o.get_all_containers()

            # patch user
            username = js.load_json(o.mapping[c_id])["user"]
            o = SocksVendor(username)

        lost_container = [i for i in o.get_user_containers() if i["container_id"] == c_id][0]
        resp = run_ss_server(
            username, pwd=lost_container["pwd"], port=lost_container["port"], enc_mode=lost_container["method"],
        )

        if resp:
            lost_container["container_id"] = resp.short_id
            lost_container["create"] = dt.datetime.today().strftime("%Y-%m-%d")

            o.add_container(lost_container)
            o.remove_container_record(c_id)
            self.set_message(req, "还原成功")

    def handle_action_new(self, username, req, fetch_request, *args, **kwargs):
        o = SocksVendor(username)

        kw = {}
        if fetch_request.get("enc"):
            kw["enc_mode"] = fetch_request["enc"]
        resp = run_ss_server(username, **kw)

        if resp:
            td = dt.datetime.today().strftime("%Y-%m-%d")
            data = dict(
                container_id=resp.short_id,
                user=username,
                create=dt.datetime.today().strftime("%Y-%m-%d"),
                pwd=resp.ext.pwd,
                method=resp.ext.enc_mode,
                port=resp.ext.port,
                more_sec=0,
                note=fetch_request.get("note", f"{username}-{td}"),
            )

            o.add_container(data)
            self.set_message(req, "创建成功")

        else:
            self.set_message(req, "创建失败，请尝试删除所有容器")


def _cover_v2ray_style_to_socks_style(data: dict) -> dict:
    meta = data["_metadata"]
    # meta = meta.replace("\'", "\"")
    # meta = json.loads(meta)

    mapping = dict(pwd="id", method="alterId", user="usr", create="ct")
    get_value = lambda k: data.get(mapping[k], meta.get(mapping[k]))

    return {k: get_value(k) for k in mapping.keys()}


class FTWAdm(SSAdm):
    login_url = "/adm/login?next=/c/ss"

    def get(self, req, *args, **kwargs):
        user = req.user
        super_admin = user.is_superuser
        username = user.username

        oS = SocksVendor(username)
        oV = V2rayVendor(username)

        if super_admin:
            sock_data = oS.get_all_containers()
            v2ray_data = oV._get_all_users()

        else:
            sock_data = oS.get_user_containers()
            v2ray_data = oV.info and [oV.info] or []

        data = v2ray_data and V2raySchema().dump(v2ray_data, many=True) or []
        data += SockSchema().dump(sock_data, many=True)

        ctx = {
            "IP": environ.get("SERVER_IP", "127.0.0.1"),
            "user": {
                "name": username,
                "is_admin": super_admin,
            },
            "ds": js.to_str(data),
            "billboard": self.get_billboard_info(),
            "message": self.flush_message(req)
        }

        return render(req, "ss/index.html", context=ctx)

    @staticmethod
    def get_user_info(req, *args, **kwargs):
        user = req.user
        super_admin = user.is_superuser
        username = user.username

        socks_proxy = SocksVendor(username)
        v2ray_proxy = V2rayVendor(username)

        if super_admin:
            sock_data = socks_proxy.get_all_containers()
            v2ray_data = v2ray_proxy._get_all_users()

        else:
            sock_data = socks_proxy.get_user_containers()
            v2ray_data = v2ray_proxy.info and [v2ray_proxy.info] or []

        data = v2ray_data and V2raySchema().dump(v2ray_data, many=True) or []
        data += SockSchema().dump(sock_data, many=True)

        return JsonResponse(dict(rv=data))

    @staticmethod
    def get_billboard_info(*args, **kwargs):
        posts = Billboard.objects \
            .filter(status=Billboard.PUBLIC) \
            .order_by("-created")

        return list(posts.values())
