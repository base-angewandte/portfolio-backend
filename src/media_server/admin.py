from django.contrib import admin

from .models import Media


class MediaAdmin(admin.ModelAdmin):
    pass


admin.site.register(Media, MediaAdmin)
