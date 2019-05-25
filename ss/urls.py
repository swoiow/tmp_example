#!/usr/bin/env python
# -*- coding: utf-8 -*

from django.conf.urls import url
from django.urls import path

from . import views


urlpatterns = [
    path("helper/<int:post_id>", views.show_billboard, name="show_billboard"),
    url(r'^api/user_data$', views.API.get_user_info),
    url(r'^v2ray$', views.V2rayAdm.as_view(), name="v2ray_adm"),
    url(r'^ss$', views.SSAdm.as_view(), name="ss_adm_default"),
    url(r'', views.SSAdm.as_view(), name="ss_adm"),
]
