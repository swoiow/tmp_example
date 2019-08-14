#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import HttpResponse

exceptions = type('exc', (object,), {})


class CodeInAvailable(HttpResponse):
    message = "无法查看此网页。或邀请码已失效。"
    status_code = 403

    def __init__(self, content=message, *args, **kwargs):
        super().__init__(content=content, *args, **kwargs)


setattr(exceptions, "CodeInAvailable", CodeInAvailable())
