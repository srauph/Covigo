from django.contrib.auth.models import User, Group, Permission
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from accounts.models import Flag


@login_required
@never_cache
def two_factor_authentication(request):
    return render(request, 'accounts/authentication/2FA.html')


@never_cache
def forgot_password(request):
    return render(request, 'accounts/authentication/forgotpassword.html')


@never_cache
def reset_password(request):
    return render(request, 'accounts/authentication/resetpassword.html')


@login_required
@never_cache
def index(request):
    return redirect('accounts:list_users')

def profile(request):
    return render(request, 'accounts/profile.html')


@login_required
@never_cache
def list_users(request):
    return render(request, 'accounts/list_users.html', {
        'users': User.objects.all()
    })


@login_required
@never_cache
def add_group(request):
    if request.method == 'POST':

        group = Group(name=request.POST['name'])
        group.save()
        permission_array = convert_permission_name_to_id(request)

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


@login_required
@never_cache
def edit_group(request, group_id):
    group = Group.objects.filter(id=group_id).get()

    if request.method == "POST":
        group.name = request.POST['name']
        group.save()
        permission_array = convert_permission_name_to_id(request)
        group.permissions.clear()
        group.permissions.set(permission_array)

        return redirect('accounts:list_group')
    else:
        return render(request, 'accounts/access_control/group/edit_group.html', {
            'permissions': Permission.objects.all(),
            'group': group
        })


def convert_permission_name_to_id(request):
    permission_array = []
    for perm in request.POST.getlist('perms'):
        permission_id = Permission.objects.filter(codename=perm).get().id
        permission_array.append(permission_id)
    return permission_array
