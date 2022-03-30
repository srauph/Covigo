from datetime import time

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.datetime_safe import datetime
from django.db.models import Q, Count
from symptoms.models import PatientSymptom
from django.db.models import Q, Count, QuerySet

from Covigo.messages import Messages
from accounts.utils import get_is_staff, send_system_message_to_user
from symptoms.models import PatientSymptom, Symptom


def get_reports_by_patient(patient_id):
    """
    Returns a queryset of reports the patient made.
    @param patient_id: the patient user id
    @return: returns a queryset of reports the patient made
    """
    criteria = Q(user_id=patient_id) & ~Q(data=None) & (Q(status=0) | Q(status=3))

    reports = PatientSymptom.objects.values('date_updated__date', 'user_id', 'is_viewed',
                                            'user__first_name', 'user__last_name',
                                            'user__patients_assigned_flags__is_active').filter(criteria).annotate(
        total_entries=Count("*")).order_by('-date_updated__date')
    return reports


def get_patient_report_information(patient_id, user, date_updated):
    """
    Gets the report information (queryset of symptoms that has been reported back to)
    which includes symptom name, the user response (data) and their name.
    @param patient_id: the patient id for the report
    @param user: the user viewing the report
    @param date_updated: date of the report
    @return: queryset of symptoms
    """
    # Patient can view updated report input only
    criteria = Q(user_id=patient_id) & ~Q(data=None) & Q(date_updated__date=date_updated) & Q(is_hidden=False)
    # Ensure staff can view all submitted updates
    if user.is_staff:
        criteria = Q(user_id=patient_id) & ~Q(data=None) & Q(date_updated__date=date_updated)

    reports = PatientSymptom.objects.values('user__first_name', 'user__last_name', 'symptom_id',
                                            'data', 'is_viewed',
                                            'symptom__name', 'id', 'date_updated', 'status', 'due_date').filter(
        criteria)
    return reports


def get_reports_for_doctor(patient_ids):
    """
    Gets a queryset for the list of reports for each patient the doctor is assigned.
    It includes past reports from previous doctors.
    @param patient_ids: list of doctor patient ids
    @return: queryset of reports
    """
    criteria = Q(user_id__in=patient_ids) & ~Q(data=None)

    reports = PatientSymptom.objects.values('date_updated__date', 'user_id', 'is_viewed',
                                            'user__first_name', 'user__last_name',
                                            'user__patients_assigned_flags__is_active').filter(criteria).annotate(
        total_entries=Count("*"))

    return reports


def check_report_exist(user_id, date):
    """
    Checks if the report exists based on the user id and date.
    @param user_id: user id of the report
    @param date: date of the report
    @return: true if the report exists otherwise false
    """
    patient_symptom = PatientSymptom.objects.all().filter(user_id=user_id, due_date__lte=date, data=None)
    return patient_symptom.exists()


def return_symptoms_for_today(user_id):
    """
    Returns a queryset of symptoms from a user id that has a report due at midnight of the current day.
    @param user_id: user id
    @return: queryset of symptoms due today
    """
    criteria = Q(user_id=user_id) & Q(due_date=datetime.combine(datetime.now(), time.max)) & Q(data=None)
    query = PatientSymptom.objects.select_related('symptom') \
        .filter(criteria) \
        .values('symptom_id', 'symptom__name', 'data', 'due_date')
    return query


def is_requested(user_id):
    """
    Checks if a doctor has requested the patient to resubmit any symptoms today.
    @param user_id: the user id
    @return: true if yes or false otherwise
    """
    criteria1 = Q(user_id=user_id) & Q(
        due_date=datetime.combine(datetime.now(), time.max))
    query = PatientSymptom.objects.filter(criteria1)

    requested_resubmit = False

    # Checks if there exists at least one instance of a doctor viewing a report + an empty data row
    # meaning a request was sent for a resubmit
    for symptoms in query:
        if symptoms.status == -2:
            # The doctor then requested a resubmit
            requested_resubmit = True
            break

    return requested_resubmit


def send_status_reminder(date=None):
    """
    Sends an email/sms to each user that has a symptom status update due either today or on the date specified
    @params: date -> allows the date being checked to be specified
    """

    if date is not None:
        statuses = PatientSymptom.objects.filter(data=None, due_date=datetime.combine(date, time.max))
        my_due_date = datetime.combine(date, time.max)
    else:
        statuses = PatientSymptom.objects.filter(data=None, due_date=datetime.combine(datetime.now(), time.max))
        my_due_date = datetime.combine(datetime.now(), time.max)

    # get user ids for the patients that have status reports due on the day
    user_ids_with_duplicates = []
    for status in statuses:
        user_ids_with_duplicates.append(status.user_id)
    user_ids_no_duplicates = list(set(user_ids_with_duplicates))

    symptoms = []
    template = Messages.STATUS_UPDATE.value
    for user_id in user_ids_no_duplicates:
        selected_user = User.objects.get(id=user_id)

        # get the all symptoms due on that day per user
        for status in statuses:
            if status.user_id == user_id:
                symptoms.append(Symptom.objects.get(id=status.symptom_id).name)
        c = {
            'date': my_due_date.date(),
            'time': my_due_date.time().replace(second=0, microsecond=0),
            'symptom': symptoms
        }

        # send email/sms to user concerning the symptoms they need to update
        send_system_message_to_user(selected_user, template=template, c=c)
        symptoms.clear()
