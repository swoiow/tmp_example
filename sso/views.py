import simplejson
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from oauth2_provider.views.generic import ProtectedResourceView


class ApiEndpoint(LoginView, ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        if request.resource_owner.is_authenticated:
            resp = dict(
                code=200,
                user=request.resource_owner.username,
            )

        else:
            resp = dict(
                code=401,
            )

        return HttpResponse(simplejson.dumps(resp), content_type="application/json")
