from django.template.loader import render_to_string
from django.urls import reverse

from messaging.models import MessageGroup


def send_notification(sender_id, recipient_id, notification_message, app_name=None, href=None):
    if not href:
        href = reverse(f"{app_name}:index")

    message_with_link = f"<a href={href}>{notification_message}</a>"

    notification = MessageGroup.objects.create(author_id=sender_id, recipient_id=recipient_id,
                                               title=message_with_link, type=1)
    notification.save()
