#!/usr/bin/env python
# -*- coding: utf-8 -*

from django.conf.urls import url

from .views import ApiEndpoint

urlpatterns = [
    url(r'^api/get_user', ApiEndpoint.as_view()),
]
