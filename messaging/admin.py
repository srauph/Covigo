from django.contrib import admin

# Register your models here.
from messaging import models
admin.site.register(models.MessageContent)
from messaging.models import MessageGroup, MessageContent

@admin.register(MessageGroup)
class MessageGroupAdmin(admin.ModelAdmin):
    pass

@admin.register(MessageContent)
class MessageContentAdmin(admin.ModelAdmin):
    pass