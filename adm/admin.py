from django.contrib import admin

admin.autodiscover()
admin.site.login_template = "adm/login.html"
admin.site.site_url = "/c/ftw/"
