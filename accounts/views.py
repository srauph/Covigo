from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


@login_required
@never_cache
def index(request):
    return redirect('accounts:list_users')


@login_required
@never_cache
def list_users(request):
    return render(request, 'accounts/list.html', {
        'users': User.objects.all()
    })

@login_required
@never_cache
def add_group(request):
    return render(request, 'accounts/access_control/group/add_group.html', {
        'permissions': Permission.objects.all()
    })


