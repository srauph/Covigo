from datetime import timedelta, date
from os import listdir, path
from os.path import join, isfile

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render

from accounts.models import Patient, Staff


CASE_DATA_PATH = "static/Covigo/data/case_data"
CONTACT_TRACING_PATH = "static/Covigo/data/contact_tracing"


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
        patient_count = User.objects.filter(is_staff=False).count()
        staff_count = User.objects.filter(is_staff=True).count()

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

    if request.method == "POST" and request.FILES["contact_tracing_file"]:
        f = request.FILES["contact_tracing_file"]


    data_files = [f for f in listdir(CONTACT_TRACING_PATH) if isfile(join(CONTACT_TRACING_PATH, f))]

    return render(request, 'manager/contact_tracing.html', {
        "data_files": data_files
    })


def case_data(request):
    if not request.user.is_staff or not request.user.has_perm("accounts.manage_case_data"):
        raise PermissionDenied

    data_files = [f for f in listdir(CASE_DATA_PATH) if isfile(join(CASE_DATA_PATH, f))]

    return render(request, 'manager/case_data.html', {
        "data_files": data_files
    })


def help_page(request):
    usr = request.user
    return render(request, 'manager/help.html', {"usr": usr})


def about(request):
    return render(request, 'manager/about.html')


def download_case_data_file(request, file_name):
    if not request.user.is_staff or not request.user.has_perm("accounts.manage_case_data"):
        raise Http404

    with open(f"{CASE_DATA_PATH}/{file_name}", 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'inline; filename=' + path.basename(file_name)
        return response


def download_contact_tracing_file(request, file_name):
    if not request.user.is_staff or not request.user.has_perm("accounts.manage_contact_tracing"):
        raise Http404

    with open(f"{CONTACT_TRACING_PATH}/{file_name}", 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'inline; filename=' + path.basename(file_name)
        return response
