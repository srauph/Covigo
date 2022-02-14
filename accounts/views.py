from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils.html import escape


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
    if request.method == 'POST':

        group = Group(name=request.POST['name'])
        group.save()
        permission_array = []

        for perm in request.POST.getlist('perms'):
            permission_id = Permission.objects.filter(codename=perm).get().id
            permission_array.append(permission_id)

        group.permissions.set(permission_array)

        return redirect('accounts:list_group')

    else:
        return render(request, 'accounts/access_control/group/add_group.html', {
            'permissions': Permission.objects.all()
        })


@login_required
@never_cache
def list_group(request):
    return render(request, 'accounts/access_control/group/list_group.html', {
        'groups': Group.objects.all()
    })
