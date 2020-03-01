#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render

from vendor import exceptions
from . import services


def smart_view(request, *args, **kwargs):
    user = request.user
    super_admin = user.is_superuser

    if super_admin:
        return HttpResponseRedirect(redirect_to="/adm")
    else:
        return HttpResponseRedirect(redirect_to="/c")


def index(request, *args, **kwargs):
    if request.method == 'GET':
        req_uid = request.GET.get("uid")
        json_data = services.load_invite_data(req_uid)

        if json_data:
            ctx = {"email": json_data["email"]}
            return render(request, "adm/join.html", context=ctx)

    elif request.method == 'POST':
        req_uid = request.GET.get("uid")
        json_data = services.load_invite_data(req_uid)

        email = json_data.get("email")
        usr, pwd = request.POST["usr"], request.POST["pwd"]

        services.create_user(username=usr, password=pwd, email=email)
        services.delete_invite_data(usr, req_uid)

        return redirect('/adm')

    return exceptions.CodeUnAvailable
