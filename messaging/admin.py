from django.contrib import admin

from messaging.models import MessageGroup, MessageContent

@admin.register(MessageGroup)
class MessageGroupAdmin(admin.ModelAdmin):
    pass

@admin.register(MessageContent)
class MessageContentAdmin(admin.ModelAdmin):
    pass