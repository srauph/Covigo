from datetime import time
from django.utils.datetime_safe import datetime
from django.db.models import Q, Count, QuerySet

from accounts.utils import get_is_staff
from symptoms.models import PatientSymptom


def get_reports_by_patient(patient_id):
    """
    Returns a queryset of reports the patient made.
    @param patient_id: the patient user id
    @return: returns a queryset of reports the patient made
    """
    criteria = Q(user_id=patient_id) & ~Q(data=None)

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
                                            'symptom__name', 'id', 'date_updated').filter(criteria)
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
    @param due_date: due date of the symptom
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
    doctor_viewed_report = False
    has_empty_data = False

    # Checks if there exists at least one instance of a doctor viewing a report + an empty data row
    # meaning a request was sent for a resubmit
    for symptoms in query:
        if symptoms.is_hidden:
            doctor_viewed_report = True
        if symptoms.data is None:
            has_empty_data = True

    # If the doctor viewed the report and there exists empty data
    if doctor_viewed_report and has_empty_data:
        # The doctor then requested a resubmit
        requested_resubmit = True

    return requested_resubmit
