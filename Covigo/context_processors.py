from django.conf import settings
from django.db.models import Q

from messaging.models import MessageGroup


def production_mode(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'PRODUCTION_MODE': settings.PRODUCTION_MODE}


def notifications(request):
    current_user = request.user

    # Fetch all received notifications
    filter1 = Q(recipient_id=current_user.id) & Q(type=1)

    all_notifications = MessageGroup.objects.filter(filter1).all()

    # Fetch unread notifications
    filter2 = Q(recipient_id=current_user.id) & Q(recipient_seen=False) & Q(type=1)

    num_of_unread_notifications = MessageGroup.objects.filter(filter2).all().count()

    return {'notifications': all_notifications,
            'num_of_unread_notifications': num_of_unread_notifications}
