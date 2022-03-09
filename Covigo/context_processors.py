from django.conf import settings


def production_mode(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'PRODUCTION_MODE': settings.PRODUCTION_MODE}
