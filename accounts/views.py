from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from accounts.models import Flag


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

  
@login_required
@never_cache
def list_group(request):
    return render(request, 'accounts/access_control/group/list_group.html', {
        'groups': Group.objects.all()
    })

  
@login_required
def flaguser(request, user_id):
    user_staff = request.user
    user_patient = User.objects.get(id=user_id)

    flag = user_staff.staffs_created_flags.filter(patient=user_patient)

    if flag:
        flag = flag.get()
        flag.is_active = True
        flag.save()
    else:
        flag = Flag(staff=user_staff, patient=user_patient, is_active=True)
        flag.save()

    return redirect("accounts:list_users")

  
@login_required
def unflaguser(request, user_id):
    user_staff = request.user
    user_patient = User.objects.get(id=user_id)

    flag = user_staff.staffs_created_flags.filter(patient=user_patient)
    if flag:
        flag = flag.get()
        flag.is_active = False
        flag.save()

    return redirect("accounts:list_users")
