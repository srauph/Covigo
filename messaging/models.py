from django.db import models
from django.contrib.auth.models import User


class MessageContent(models.Model):
    author = models.ManyToManyField(
        User,
        related_name="authors",
        through='MessageTitle',
        through_fields=('')
    )


class MessageTitle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message_content = models.ForeignKey(MessageContent, on_delete=models.CASCADE)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'message_content'], name='')
        ]

