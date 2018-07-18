from django.contrib import admin

admin.autodiscover()
admin.site.login_template = "adm_login.html"
