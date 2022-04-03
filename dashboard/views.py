import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from accounts.models import Staff
from appointments.models import Appointment
from dashboard.utils import fetch_data_from_file, extract_daily_data
from messaging.models import MessageGroup
from status.utils import return_symptoms_for_today, is_requested


@login_required
@never_cache
def index(request):
    user = request.user

    messages = fetch_messaging_info(user)
    appointments = fetch_appointments_info(user)

    if user.is_staff:
        recent_status_updates = []
        if not user.is_superuser and user.has_perm("accounts.is_doctor"):
            assigned_patients = user.staff.get_assigned_patient_users()
        else:
            assigned_patients = []

        covigo_case_data = fetch_data_from_all_files()

        return render(request, 'dashboard/index.html', {
            "messages": messages,
            "appointments": appointments,
            "recent_status_updates": recent_status_updates,
            "assigned_patients": assigned_patients,
            "covigo_case_data": covigo_case_data,
        })

    else:
        status_reminder = fetch_status_reminder_info(user)
        case = fetch_own_case_info(user)
        assigned_doctor = user.patient.get_assigned_staff_user()

        return render(request, 'dashboard/index.html', {
            "messages": messages,
            "appointments": appointments,
            "status_reminder": status_reminder,
            "case": case,
            "assigned_doctor": assigned_doctor,
        })


def fetch_messaging_info(user):
    msg_group_filter = Q(author=user) | Q(recipient=user)
    all_messages = MessageGroup.objects.filter(msg_group_filter)

    urgent_msg_group_filter = msg_group_filter & Q(priority=2)
    urgent = all_messages.filter(urgent_msg_group_filter)

    unread_msg_group_filter = (Q(author=user) & Q(author_seen=False)) | (Q(recipient=user) & Q(recipient_seen=False))
    unread = all_messages.filter(unread_msg_group_filter)
    unread_urgent = urgent.filter(unread_msg_group_filter)

    return {
        "all": all_messages,
        "urgent": urgent,
        "unread": unread,
        "unread_urgent": unread_urgent,
    }


def fetch_appointments_info(user):
    now = datetime.datetime.now()
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    in_two_days = tomorrow + datetime.timedelta(days=1)

    all_filter = Q(patient__isnull=False) & Q(start_date__gte=now)
    today_filter = Q(start_date__gte=now) & Q(start_date__lt=tomorrow)
    tomorrow_filter = Q(start_date__gte=tomorrow) & Q(start_date__lt=in_two_days)

    if user.is_staff:
        all_appointments = Appointment.objects.filter(staff=user).filter(all_filter).order_by("start_date")
    else:
        all_appointments = Appointment.objects.filter(patient=user).filter(all_filter)

    today_appointments = all_appointments.filter(today_filter)
    tomorrow_appointments = all_appointments.filter(tomorrow_filter)

    return {
        "all": all_appointments,
        "today": today_appointments,
        "tomorrow": tomorrow_appointments,
    }


def fetch_data_from_all_files(data_path="dashboard/sample_data"):
    confirmed = fetch_data_from_file(f"{data_path}/confirmed_cases.csv")
    daily_confirmed = extract_daily_data(confirmed)

    current_positives = fetch_data_from_file(f"{data_path}/positive_cases.csv")
    daily_positives = extract_daily_data(current_positives)

    recoveries = fetch_data_from_file(f"{data_path}/recovered_cases.csv")
    daily_recoveries = extract_daily_data(recoveries)

    unconfirmed_negative = fetch_data_from_file(f"{data_path}/unconfirmed_negative.csv")
    daily_unconfirmed_negative = extract_daily_data(unconfirmed_negative)

    unconfirmed_untested = fetch_data_from_file(f"{data_path}/unconfirmed_untested.csv")
    daily_unconfirmed_untested = extract_daily_data(unconfirmed_untested)

    return {
        "confirmed": confirmed,
        "daily_confirmed": daily_confirmed,
        "current_positives": current_positives,
        "daily_positives": daily_positives,
        "recoveries": recoveries,
        "daily_recoveries": daily_recoveries,
        "unconfirmed_negative": unconfirmed_negative,
        "daily_unconfirmed_negative": daily_unconfirmed_negative,
        "unconfirmed_untested": unconfirmed_untested,
        "daily_unconfirmed_untested": daily_unconfirmed_untested,
    }


def fetch_status_reminder_info(user):
    patient_symptoms = return_symptoms_for_today(user.id)
    is_resubmit_requested = is_requested(user.id)

    return {
        "is_reporting_today": patient_symptoms.exists(),
        "is_resubmit_requested": is_resubmit_requested,
    }


def fetch_own_case_info(user):
    return {
        "is_quarantining": user.patient.is_quarantining,
        "is_positive": user.patient.is_confirmed and not user.patient.is_negative,
        "is_negative": user.patient.is_negative,
    }
