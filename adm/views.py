#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json as js

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from redis import StrictRedis

from adm.apps import AdmConfig


def smart_view(request, *args, **kwargs):
    user = request.user
    super_admin = user.is_superuser

    if super_admin:
        return HttpResponseRedirect(redirect_to="/adm")
    else:
        return HttpResponseRedirect(redirect_to="/ss")


def index(request, *args, **kwargs):
    rds = StrictRedis(host=AdmConfig.rds_host, port=AdmConfig.rds_port, socket_keepalive=10, db=1)

    if request.method == 'GET':
        req_uid = request.GET.get("uid")
        data = rds.get(req_uid)

        if data:
            data = js.loads(data)
            ctx = {"email": data["email"]}
            return render(request, "adm/join.html", context=ctx)

    elif request.method == 'POST':
        req_uid = request.GET.get("uid")
        data = rds.get(req_uid)
        data = js.loads(data)

        email = data.get("email")
        usr, pwd = request.POST["usr"], request.POST["pwd"]

        new_user = User.objects.create_user(username=usr, password=pwd, email=email, is_staff=True)
        new_user.save()

        if User.objects.filter(username=usr).count() >= 1:
            rds.delete(req_uid)

        return redirect('/adm')

    return HttpResponse(status=403)
