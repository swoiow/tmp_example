#!/usr/bin/env python
# -*- coding: utf-8 -*

from django.conf.urls import url
from django.urls import path

from . import views


urlpatterns = [
    path("helper/<int:post_id>", views.show_billboard, name="show_billboard"),
    url(r'^$', views.SSAdm.as_view()),
]
