import simplejson
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import render
from oauth2_provider.views.generic import ProtectedResourceView


def index(request, *_):
    return render(request, "cas_index.html")


def nginx_auth(request):
    if not request.user.is_authenticated:
        return HttpResponse(request.META["REMOTE_ADDR"] + ": Unauthorized", status=401)
    else:
        return HttpResponse(request.user.username, status=200)


class ApiEndpoint(LoginView, ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        if request.resource_owner.is_authenticated:
            resp = dict(
                user=request.resource_owner.username,
                ip=request.META["REMOTE_ADDR"],
            )
            return HttpResponse(simplejson.dumps(resp), content_type="application/json")

        else:
            return HttpResponse(status=401)
