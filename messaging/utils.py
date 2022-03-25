from messaging.models import MessageGroup


def send_notification(sender_id, recipient_id, notification_message):
    notification = MessageGroup.objects.create(author_id=sender_id, recipient_id=recipient_id,
                                               title=notification_message, type=1)
    notification.save()
