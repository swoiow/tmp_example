#!/usr/bin/env python
# -*- coding: utf-8 -*

from django.conf.urls import url

from .views import ApiEndpoint, nginx_auth

urlpatterns = [
    url(r'^api/get_user', ApiEndpoint.as_view()),
    url(r'^api/nginx', nginx_auth),
]
