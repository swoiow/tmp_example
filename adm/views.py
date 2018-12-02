#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json as js
from os import environ

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect, render
from redis import StrictRedis


def index(request, *args, **kwargs):
    rds = StrictRedis(host=environ["REDIS"], socket_keepalive=10, db=1)

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

        return redirect('%s?next=/ss' % settings.LOGIN_URL)

    return HttpResponse(status=403)
