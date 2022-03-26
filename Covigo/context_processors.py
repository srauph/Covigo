from django.conf import settings
from django.db.models import Q

from messaging.models import MessageGroup


def production_mode(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'PRODUCTION_MODE': settings.PRODUCTION_MODE}

