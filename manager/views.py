import csv
import io
import os
from datetime import timedelta, date
from os import listdir, path
from os.path import join, isfile
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render

from accounts.models import Patient, Staff, Profile
from accounts.utils import get_or_generate_patient_code

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

    contact_tracing_path = Path(CONTACT_TRACING_PATH)
    ensure_path_exists(contact_tracing_path)

    if request.method == "POST" and request.FILES["contact_tracing_file"]:
        f = request.FILES["contact_tracing_file"]

        if f.name[-4:] == ".csv":
            save_contact_tracing_csv_file(f)

            with open(Path(join(CONTACT_TRACING_PATH, f.name)), "r") as contact_tracing_file:
                reader = csv.DictReader(contact_tracing_file)
                data = list(reader)
                create_users_from_csv_date(request, data)

            messages.success(request, 'File uploaded and processed successfully!')

        else:
            messages.error(request, 'Invalid File Format: Please upload a csv file.')

    data_files = [f for f in listdir(CONTACT_TRACING_PATH) if isfile(join(CONTACT_TRACING_PATH, f))]

    return render(request, 'manager/contact_tracing.html', {
        "data_files": data_files
    })


def case_data(request):
    if not request.user.is_staff or not request.user.has_perm("accounts.manage_case_data"):
        raise PermissionDenied

    contact_tracing_path = Path(CASE_DATA_PATH)
    ensure_path_exists(contact_tracing_path)

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


def save_contact_tracing_csv_file(f):
    file_name = Path(join(CONTACT_TRACING_PATH, f.name))
    if file_name.exists():
        old_name = str(file_name)
        i = 1
        while Path(f"{old_name[:-4]}__{i}{old_name[-4:]}").exists():
            i += 1
        file_name = Path(f"{old_name[:-4]}__{i}{old_name[-4:]}")

    with open(file_name, 'wb') as file_to_save:
        file_to_save.write(f.file.read())
        file_to_save.close()


def create_users_from_csv_date(request, data):
    for entry in data:
        first_name = entry["First Name"]
        last_name = entry["Last Name"]
        email = entry["Email"]
        phone = entry["Phone Number"]

        if not first_name:
            first_name = ""
        if not last_name:
            last_name = ""
        if not email:
            email = ""
        if not phone:
            phone = ""

        if email != "" and User.objects.filter(email=email).exists():
            messages.warning(request, f"Unable to make user: Could not make user with information {first_name}, {last_name}, {email}, {phone}: User with email {email} already exists.")
            continue
        else:
            if email != "":
                if not User.objects.filter(username=email).exists():
                    new_username = email
                else:
                    new_username = f"{email}-{1 + User.objects.filter(username__startswith=email).count()}"
            elif phone != "":
                if not User.objects.filter(username=phone).exists():
                    new_username = phone
                else:
                    new_username = f"{phone}-{1 + User.objects.filter(username__startswith=phone).count()}"
            else:
                messages.warning(request, f"Unable to make user: Could not make user with information {first_name}, {last_name}, {email}, {phone}.")
                continue

        u = User.objects.create(username=new_username, first_name=first_name, last_name=last_name, email=email)
        Profile.objects.filter(user=u).update(phone_number=phone)
        p = Patient.objects.create(user=u)
        get_or_generate_patient_code(p, prefix="T")


def ensure_path_exists(path_to_check):
    if not Path.exists(path_to_check):
        Path.mkdir(path_to_check, exist_ok=True)
    elif Path.is_file(path_to_check):
        i = 1
        while Path.exists(Path(f"{path_to_check}_{i}")):
            i += 1
        Path.rename(path_to_check, Path(f"{path_to_check}_{i}"))
        Path.mkdir(path_to_check, exist_ok=True)