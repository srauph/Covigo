from django.contrib.auth.models import User
from django.shortcuts import render


def userlist(request):
    return render(request, 'accounts/list.html', {
        'users': User.objects.all()
    })


def justGetAStaffForNowIdcAbtAnythingElse(user_id):
    user = User.objects.get(pk=user_id)
    return user
