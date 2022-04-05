from django.contrib import admin

# Register your models here.
from messaging import models
admin.site.register(models.MessageContent)