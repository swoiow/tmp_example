#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib.auth.mixins import LoginRequiredMixin as _LoginRequiredMixin
from django.views.generic import View as _djangoView


class MessageView(object):

    def set_message(self, request, message, *args, **kwargs):
        request.session["msg_box"] = message

    def flush_message(self, request, *args, **kwargs):
        return "msg_box" in request.session and request.session.pop("msg_box")


class LoginRequiredMixin(MessageView, _LoginRequiredMixin, _djangoView):
    pass
