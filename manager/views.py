import csv
import io
import json
import os
import threading

from datetime import timedelta, date
from os import listdir, path
from os.path import join, isfile
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Permission
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache

from Covigo.feature_toggles import FeatureToggles
from Covigo.messages import Messages
from accounts.models import Patient, Staff, Profile
from accounts.utils import get_or_generate_patient_code, send_system_message_to_user, \
    get_distance_of_all_doctors_to_postal_code, get_assigned_staff_id_by_patient_id
from appointments.utils import rebook_appointment_with_new_doctor
from messaging.utils import send_notification

CASE_DATA_PATH = "static/Covigo/data/case_data"
CONTACT_TRACING_PATH = "static/Covigo/data/contact_tracing"


@login_required
@never_cache
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


@login_required
@never_cache
def contact_tracing(request):
    if not request.user.is_staff or not request.user.has_perm("accounts.manage_contact_tracing"):
        raise PermissionDenied
    contact_tracing_path = Path(CONTACT_TRACING_PATH)
    ensure_path_exists(contact_tracing_path)
    failed_entries = []

    if "tracing_uploads" in request.session:
        uploads = request.session.pop("tracing_uploads")
        for i in uploads:
            if uploads[i] == "Success":
                messages.success(request, f"All entries in file {i} were entered successfully!")
            elif uploads[i] == "Failure":
                messages.error(request, f"Failed to process file {i}: Some or all of the data could not be read. You may try again; if the problem persists, the file may be corrupted.")
            elif uploads[i] == "Empty":
                messages.error(request, f"Failed to process file {i}: The file is empty. If this is not the case, you may try again; if the problem persists, the file may be corrupted.")
            else:
                failed_entries = uploads[i]
                messages.warning(request, f"The following {len(failed_entries)} entries in file {i} failed to import:")

    if request.method == "POST" and request.FILES["contact_tracing_file"]:
        f = request.FILES["contact_tracing_file"]

        if f.name[-4:] == ".csv":
            file_name = save_contact_tracing_csv_file(f)

            with open(Path(join(CONTACT_TRACING_PATH, file_name)), "r") as contact_tracing_file:
                reader = csv.DictReader(contact_tracing_file)
                data = list(reader)
                t = threading.Thread(target=process_contact_tracing_csv, args=[request, data, file_name])
                t.daemon = True
                t.start()

            if file_name == f.name:
                messages.success(request, f"File {f.name} uploaded successfully!")
            else:
                messages.success(request, f"File {f.name} uploaded successfully as {file_name}!")

        else:
            messages.error(request, 'Invalid File Format: Please upload a csv file.')

    return render(request, 'manager/contact_tracing.html', {
        "failed_entries": failed_entries
    })


@login_required
@never_cache
def contact_tracing_table(request):
    if not request.user.is_staff or not request.user.has_perm("accounts.manage_contact_tracing"):
        raise PermissionDenied

    data_files = [f for f in listdir(CONTACT_TRACING_PATH) if isfile(join(CONTACT_TRACING_PATH, f))]

    # Deprecated for now. May be re-instated later.
    #
    # if 'Search by File Name' in request.GET:
    #     search_data_file_name_term = request.GET['Search by File Name']
    #     if search_data_file_name_term == '':
    #         data_files_search_result = [f for f in listdir(CONTACT_TRACING_PATH) if isfile(join(CONTACT_TRACING_PATH, f))]
    #     else:
    #         data_files_search_result = filter(lambda data_file: data_file == search_data_file_name_term, data_files)
    #
    #     return render(request, 'manager/contact_tracing.html', {
    #         'data_files_search_result': data_files_search_result
    #     })

    files_table = list(map(lambda x: {"name": x}, data_files))

    serialized_files = json.dumps({'data': files_table}, indent=4)

    return HttpResponse(serialized_files, content_type='application/json')


@login_required
@never_cache
def case_data(request):
    if not request.user.is_staff or not request.user.has_perm("accounts.manage_case_data"):
        raise PermissionDenied

    contact_tracing_path = Path(CASE_DATA_PATH)
    ensure_path_exists(contact_tracing_path)

    data_files = [f for f in listdir(CASE_DATA_PATH) if isfile(join(CASE_DATA_PATH, f))]

    return render(request, 'manager/case_data.html', {
        "data_files": data_files
    })


@login_required
@never_cache
def help_page(request):
    usr = request.user
    return render(request, 'manager/help.html', {"usr": usr})


@login_required
@never_cache
def about(request):
    return render(request, 'manager/about.html')


@login_required
@never_cache
def download_case_data_file(request, file_name):
    if not request.user.is_staff or not request.user.has_perm("accounts.manage_case_data"):
        raise Http404

    with open(f"{CASE_DATA_PATH}/{file_name}", 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'inline; filename=' + path.basename(file_name)
        return response


@login_required
@never_cache
def download_contact_tracing_file(request, file_name):
    if not request.user.is_staff or not request.user.has_perm("accounts.manage_contact_tracing"):
        raise Http404

    with open(f"{CONTACT_TRACING_PATH}/{file_name}", 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'inline; filename=' + path.basename(file_name)
        return response


def save_contact_tracing_csv_file(f):
    file_name = Path(join(CONTACT_TRACING_PATH, f.name))
    file_existed = False
    i = 1
    if file_name.exists():
        file_existed = True
        old_name = str(file_name)
        while Path(f"{old_name[:-4]}__{i}{old_name[-4:]}").exists():
            i += 1
        file_name = Path(f"{old_name[:-4]}__{i}{old_name[-4:]}")

    with open(file_name, 'wb') as file_to_save:
        file_to_save.write(f.file.read())
        file_to_save.close()

    if file_existed:
        return f"{f.name[:-4]}__{i}{f.name[-4:]}"
    else:
        return f.name


def create_users_from_csv_date(request, data):
    if not data:
        return "Empty"

    failed_entries = []
    line = 0

    try:
        for entry in data:
            line += 1
            first_name = entry["First Name"]
            last_name = entry["Last Name"]
            email = entry["Email"]
            phone = entry["Phone Number"]

            existing_filter = Q()

            if not first_name:
                first_name = ""
            else:
                existing_filter &= Q(first_name=first_name)

            if not last_name:
                last_name = ""
            else:
                existing_filter &= Q(last_name=last_name)

            if not email:
                email = ""
            else:
                existing_filter &= Q(email=email)

            if not phone:
                phone = ""
            else:
                existing_filter &= Q(profile__phone_number=phone)

            if first_name == "" and last_name == "" and email == "" and phone == "":
                failed_entry = f"Line {line}: First name: {first_name}, Last name: {last_name}, Email: {email}, Phone number: {phone} -- Failed: This entry contains no data."
                failed_entries.append(failed_entry)
                continue

            if email == "" and phone == "":
                failed_entry = f"Line {line}: First name: {first_name}, Last name: {last_name}, Email: {email}, Phone number: {phone} -- Failed: Entry lacks both email and phone number."
                failed_entries.append(failed_entry)
                continue

            if User.objects.filter(existing_filter).exists():
                failed_entry = f"Line {line}: First name: {first_name}, Last name: {last_name}, Email: {email}, Phone number: {phone} -- Failed: A user with the exact same entry data already exists."
                failed_entries.append(failed_entry)
                continue

            if email != "" and User.objects.filter(email=email).exists():
                failed_entry = f"Line {line}: First name: {first_name}, Last name: {last_name}, Email: {email}, Phone number: {phone} -- Failed: Email address in email already in use."
                failed_entries.append(failed_entry)
                continue

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
                continue

            u = User.objects.create(username=new_username, first_name=first_name, last_name=last_name, email=email)
            Profile.objects.filter(user=u).update(phone_number=phone)
            p = Patient.objects.create(user=u)
            get_or_generate_patient_code(p, prefix="T")

            if FeatureToggles.SEND_SYSTEM_MESSAGES_TO_NEW_TRACED_USERS:
                template = Messages.REGISTER_USER.value
                c = {
                    'token': default_token_generator.make_token(u),
                }

                send_system_message_to_user(u, template=template, c=c)

    except Exception:
        return "Failure"

    return failed_entries


def ensure_path_exists(path_to_check):
    if not Path.exists(path_to_check):
        Path.mkdir(path_to_check, exist_ok=True)
    elif Path.is_file(path_to_check):
        i = 1
        while Path.exists(Path(f"{path_to_check}_{i}")):
            i += 1
        Path.rename(path_to_check, Path(f"{path_to_check}_{i}"))
        Path.mkdir(path_to_check, exist_ok=True)


def process_contact_tracing_csv(request, data, filename):
    failed_entries = create_users_from_csv_date(request, data)

    if "tracing_uploads" not in request.session:
        request.session["tracing_uploads"] = {}

    if failed_entries:
        if failed_entries == "Empty":
            request.session["tracing_uploads"][filename] = "Empty"
        elif failed_entries == "Failure":
            request.session["tracing_uploads"][filename] = "Failure"
        else:
            request.session["tracing_uploads"][filename] = failed_entries
    else:
        request.session["tracing_uploads"][filename] = "Success"

    request.session.modified = True
    request.session.save()

    href = reverse('manager:contact_tracing')
    send_notification(
        request.user.id,
        request.user.id,
        f"Your contact tracing file {filename} has finished importing",
        href=href
    )


def doctor_patient_list(request):
    if not request.user.has_perm("accounts.edit_assigned_doctor"):
        raise PermissionDenied

    return render(request, 'manager/doctors.html')


def doctor_patient_list_table(request):
    # TODO FILTER FOR DOCTORS ONLY (Currently anyone in accounts_staff is treated as a doctor for the query)
    if not request.user.has_perm("accounts.edit_assigned_doctor"):
        raise PermissionDenied

    query = get_doctors_list()

    # Serialize the JSON from the query
    serialized_reports = json.dumps({'data': query}, indent=4)

    return HttpResponse(serialized_reports, content_type='application/json')


def reassign_doctor(request, user_id):
    user = User.objects.get(id=user_id)

    if user.is_staff:
        raise Http404

    if request.method == "POST":
        doctor_user_id = request.POST.get('new_doctor_id')

        if doctor_user_id == "-1":
            user.patient.assigned_staff = None
            messages.success(request, "This patient was unassigned from their doctor successfully.")
        else:
            # rebooks previously booked appointments with the old doctor with the new doctor if the new doctor has
            # an availability at the same day and time as the previously booked appointment
            rebook_appointment_with_new_doctor(doctor_user_id, user.patient.get_assigned_staff_user().id, user)
            user.patient.assigned_staff_id = Staff.objects.get(user_id=doctor_user_id)
            messages.success(request, "This patient was assigned to the new doctor successfully.")
        user.patient.save()

    assigned_staff = user.patient.get_assigned_staff_user()

    return render(request, 'manager/reassign_doctor.html', {
        "user_id": user_id,
        "assigned_staff": assigned_staff,
    })


def reassign_doctor_list_table(request, user_id):
    if not request.user.has_perm("accounts.edit_assigned_doctor"):
        raise PermissionDenied

    user = User.objects.get(id=user_id)

    if user.is_staff:
        raise Http404

    postal_code = user.profile.postal_code

    docs_list = get_distance_of_all_doctors_to_postal_code(postal_code)

    # Build JSON
    docs_table = []
    for i in docs_list:
        docs_table.append({
            "doc_id": i[0].id,
            "first_name": i[0].first_name,
            "last_name": i[0].last_name,
            "distance": i[1],
            "patient_count": i[2],
        })

    # Serialize the JSON from the query
    serialized_docs = json.dumps({'data': docs_table}, indent=4)

    return HttpResponse(serialized_docs, content_type='application/json')


def get_doctors_list():
    """
    Raw query to get each doctor and their patient count
    @return: Queryset of all doctors
    """

    # Old raw query. Didn't work properly (cont returns 1 instead of 0 when filtered to include 0s;
    # or didn't return doctors with 0 assigned patients when filtered to exclude 0s)
    #
    # query = Staff.objects.raw(
    #     "SELECT `auth_user`.`id`, `auth_user`.`first_name`, `auth_user`.`last_name`, `accounts_staff`.`user_id`, COUNT(*) AS patient_count FROM `accounts_staff` LEFT JOIN `accounts_patient` ON (`accounts_staff`.`id` = `accounts_patient`.`assigned_staff_id`) LEFT OUTER JOIN `auth_user` ON (`accounts_staff`.`user_id` = `auth_user`.`id`) GROUP BY `accounts_patient`.`assigned_staff_id` ORDER BY `auth_user`.`first_name` , `auth_user`.`last_name`"
    # )

    doctor_perm = Permission.objects.get(codename="is_doctor")
    query = User.objects.filter(user_permissions=doctor_perm).values(
        "id",
        "first_name",
        "last_name",
        "staff__id",
    ).annotate(patient_count=Count("staff__assigned_patients"))

    return list(query)
