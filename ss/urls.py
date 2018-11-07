#!/usr/bin/env python
# -*- coding: utf-8 -*

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^proxy', views.proxy),
    url(r'^help', views.helper),
    url(r'', views.SSAdm.as_view()),
]
