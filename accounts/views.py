from django.contrib.auth.models import User
from django.shortcuts import render


def userlist(request):
    return render(request, 'accounts/list.html', {
        'users': User.objects.all()
    })
