from django.contrib import admin

# Register your models here.


from .models import *


class PerConfig(admin.ModelAdmin):
    list_display = ["title", "url", "action", "group"]


admin.site.register(User)
admin.site.register(Role)
admin.site.register(Permission, PerConfig)
admin.site.register(PermissionGroup)

