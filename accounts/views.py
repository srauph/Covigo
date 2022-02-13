from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


@login_required
@never_cache
def user_list(request):
    return render(request, 'accounts/list.html', {
        'users': User.objects.all()
    })
