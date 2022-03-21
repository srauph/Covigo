from datetime import time
from django.utils.datetime_safe import datetime
from django.db.models import Q, Count, QuerySet
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


def get_patient_report_information(user_id, date_updated):
    """
    Gets the report information (queryset of symptoms that has been reported back to)
    which includes symptom name, the user response (data) and their name.
    @param user_id:
    @param date_updated:
    @return: queryset of symptoms
    """
    criteria = Q(user_id=user_id) & ~Q(data=None) & Q(date_updated__date=date_updated)

    reports = PatientSymptom.objects.values('user__first_name', 'user__last_name', 'symptom_id',
                                            'data', 'is_viewed',
                                            'symptom__name', 'id').filter(criteria)
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
