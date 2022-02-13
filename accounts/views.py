from django.contrib.auth.models import User
from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def userlist(request):
    return render(request, 'accounts/list.html', {
        'users': User.objects.all()
    })
