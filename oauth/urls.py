"""oauth URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls import include, static, url
from django.contrib import admin
from django.urls import path

from cas import views as cas_view


urlpatterns = [
    path('adm/', admin.site.urls, name="adm"),
    url(r'^static/(?P<path>.*)$', static.serve, {'document_root': settings.STATIC_ROOT}),
]

urlpatterns += [
    url(r'^cas/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^v1/', include('cas.urls')),
    url(r'^(index|)+$', cas_view.index),
    url(r'^ss/', include('ss.urls')),
]
