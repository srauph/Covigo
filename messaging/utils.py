from django.template.loader import render_to_string
from django.urls import reverse

from messaging.models import MessageGroup


def send_notification(sender_id, recipient_id, notification_message, app_name=None, href=None):
    """
    Utility function to send notifications.
    Developer needs to only add one of either the app_name or the href input.
    Specify the app name if you want the user to be redirected to the index page of the app after clicking the
    notification. Specify the href if you want the user to be redirected to a specific page of the app,
    such as a specific message group that requires an id, after clicking the notification.

    @param sender_id:  id of user who initiated the notification creation
    @param recipient_id: id of user who is receiving the new notification
    @param notification_message: Description of the notification
    @param app_name: The name of the app to be redirected to the index page, such as messaging, appointments, etc.
    @param href: Format should be for example: href = reverse('messaging:view_message', args=[12])
    @return: status index page or 404 if user is not a staff

    """
    if not href:
        href = reverse(f"{app_name}:index")

    # Adding the href directly to the message group title text
    message_with_link = f"<a href={href}>{notification_message}</a>"

    notification = MessageGroup.objects.create(author_id=sender_id, recipient_id=recipient_id,
                                               title=message_with_link, type=1)
    notification.save()
