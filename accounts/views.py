from django.contrib.auth.models import User
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
def flaguser(request, user_id):

    user_staff = request.user
    user_patient = User.objects.get(id=user_id)

    flag = user_staff.staffs_created_flags.filter(patient=user_patient)

    if flag:
        flag = flag.get()
        print(f"Flag exists")
        flag.is_active = True
        flag.save()
    else:
        print("doesnt exist")
        flag = Flag(staff=user_staff, patient=user_patient, is_active=True)
        flag.save()

    return redirect("accounts:list_users")
