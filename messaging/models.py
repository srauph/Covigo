from django.db import models
from django.contrib.auth.models import User


class MessageGroup(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='authored_messages'
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='received_messages'
    )
    title = models.TextField(blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)
    seen = models.BooleanField(blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    date_updated = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title


class MessageContent(models.Model):
    message = models.ForeignKey(
        MessageGroup,
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='+'
    )
    content = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    date_updated = models.DateTimeField(blank=True, null=True)

