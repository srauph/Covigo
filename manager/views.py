from datetime import timedelta, date

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from accounts.models import Patient, Staff


def index(request):

    can_view_any_quicklink = (
        request.user.has_perm("accounts.manage_symptoms")
        or request.user.has_perm("accounts.edit_assigned_doctor")
        or request.user.has_perm("accounts.manage_contact_tracing")
        or request.user.has_perm("accounts.manage_case_data")
    )

    if not request.user.is_staff or (
        not can_view_any_quicklink
        and not request.user.has_perm("accounts.view_manager_data")
    ):
        raise PermissionDenied
    
    if request.user.has_perm("accounts.view_manager_data"):
        user_count = User.objects.count()
        patient_count = Patient.objects.count()
        staff_count = Staff.objects.count()

        today = date.today()
        yesterday = today - timedelta(days=1)
        new_users_yesterday = User.objects.filter(date_joined__date=yesterday).count()
    else:
        user_count = None
        patient_count = None
        staff_count = None
        new_users_yesterday = None

    return render(request, 'manager/index.html', {
        "user_count": user_count,
        "patient_count": patient_count,
        "staff_count": staff_count,
        "new_users_yesterday": new_users_yesterday,
        "perms_view_quicklinks": can_view_any_quicklink,
    })


def contact_tracing(request):
    if not request.user.is_staff or not request.user.has_perm("accounts.manage_contact_tracing"):
        raise PermissionDenied

    user_count = User.objects.count()
    return render(request, 'manager/contact_tracing.html', {"user_count": user_count})


def help_page(request):
    usr = request.user
    return render(request, 'manager/help.html', {"usr": usr})
