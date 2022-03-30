from django.db import models
from django.contrib.auth.models import User


# Info for field "type": This implementation increases the flexibility of the MessageGroup model in case a new
# feature is to be added in the future.
# 0 -> MessageGroup object for message group.
# 1 -> MessageGroup object for notifications.
class MessageGroup(models.Model):
    author = models.ForeignKey(
        User,
        related_name='authored_messages',
        on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        User,
        related_name='received_messages',
        on_delete=models.CASCADE
    )
    title = models.TextField(blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)
    author_seen = models.BooleanField(default=False)
    recipient_seen = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    type = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.title


class MessageContent(models.Model):
    message = models.ForeignKey(
        MessageGroup,
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='+',
        on_delete=models.CASCADE
    )
    content = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # TODO make str method
