#!/usr/bin/env python
# -*- coding: utf-8 -*

from django.conf.urls import url
from django.urls import path

from . import views


urlpatterns = [
    path("helper/<int:post_id>", views.show_billboard, name="show_billboard"),
    url(r'^api/user_data$', views.FTWAdm.get_user_info),
    url(r'^api/v2ray_restart$', views.V2rayAdm.restart_container),
    url(r'^v2ray$', views.V2rayAdm.as_view(), name="v2ray_adm"),
    url(r'^ss$', views.FTWAdm.as_view(), name="ftw_default"),
    url(r'', views.FTWAdm.as_view(), name="ftw_adm"),
]
