from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.cache import never_cache

from appointments.models import Appointment
from dashboard.utils import fetch_data_from_file, extract_daily_data
from messaging.models import MessageGroup

@login_required
@never_cache
def index(request):
    user = request.user

    messages = fetch_messaging_info(user)
    appointments = fetch_appointments_info(user)

    if user.is_staff:
        appointments = Appointment.objects.filter(patient=user)
        recent_status_updates = []
        assigned_patients = user.staff.get_assigned_patient_users()
        data = fetch_data_from_all_files()

        return render(request, 'dashboard/index.html', {
            "messages": messages,
            "appointments": appointments,
            "recent_status_updates": recent_status_updates,
            "assigned_patients": assigned_patients,
            "data": data,
        })

    else:
        status_reminder = []
        quarantine = []
        assigned_doctor = user.patient.get_assigned_staff_user()

        return render(request, 'dashboard/index.html', {
            "messages": messages,
            "appointments": appointments,
            "status_reminder": status_reminder,
            "quarantine": quarantine,
            "assigned_doctor": assigned_doctor,
        })


def fetch_messaging_info(user):
    msg_group_filter = Q(author=user) | Q(recipient=user)
    all = MessageGroup.objects.filter(msg_group_filter)

    urgent_msg_group_filter = msg_group_filter & Q(priority=2)
    urgent = all.filter(urgent_msg_group_filter)

    unread_msg_group_filter = (Q(author=user) & Q(author_seen=False)) | (Q(recipient=user) & Q(recipient_seen=False))
    unread = all.filter(unread_msg_group_filter)
    unread_urgent = urgent.filter(unread_msg_group_filter)

    return {
        "all": all,
        "urgent": urgent,
        "unread": unread,
        "unread_urgent": unread_urgent,
    }


def fetch_appointments_info(user):
    if user.is_staff:
        all = Appointment.objects.filter(staff=user)
    else:
        all = Appointment.objects.filter(patient=user)

    return {
        "all": all,
    }


def fetch_data_from_all_files():
    confirmed = fetch_data_from_file("dashboard/data/confirmed_cases.csv")
    daily_confirmed = extract_daily_data(confirmed)

    current_positives = fetch_data_from_file("dashboard/data/positive_cases.csv")
    daily_positives = extract_daily_data(current_positives)

    recoveries = fetch_data_from_file("dashboard/data/recovered_cases.csv")
    daily_recoveries = extract_daily_data(recoveries)

    unconfirmed_negative = fetch_data_from_file("dashboard/data/unconfirmed_negative.csv")
    daily_unconfirmed_negative = extract_daily_data(unconfirmed_negative)

    unconfirmed_untested = fetch_data_from_file("dashboard/data/unconfirmed_untested.csv")
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
