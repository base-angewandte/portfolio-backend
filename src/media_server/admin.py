from django.contrib import admin

from . import models


class AudioAdmin(admin.ModelAdmin):
    pass


class DocumentAdmin(admin.ModelAdmin):
    pass


class ImageAdmin(admin.ModelAdmin):
    pass


class VideoAdmin(admin.ModelAdmin):
    pass

class OtherAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Audio, AudioAdmin)
admin.site.register(models.Document, DocumentAdmin)
admin.site.register(models.Image, ImageAdmin)
admin.site.register(models.Video, VideoAdmin)
admin.site.register(models.Other, OtherAdmin)
