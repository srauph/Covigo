from datetime import time
from django.db.models import Q
from django.utils.datetime_safe import datetime
from symptoms.models import PatientSymptom


def return_reports(patient_ids, staff_id):
    """
    Returns a queryset of reports for the patient from the staff.
    @param patient_ids: the patient user id
    @param staff_id: the user id of the assigned staff
    @return: returns a queryset of reports for the patient from the staff
    """
    criteria = Q(user_id__in=patient_ids) & Q(user__patients_assigned_flags__staff_id=staff_id)

    reports = PatientSymptom.objects.select_related('user').filter(criteria) \
        .values('date_updated__date', 'user_id', 'is_viewed', 'user__first_name', 'user__last_name',
                'user__patients_assigned_flags__is_active', 'user__patients_assigned_flags__staff_id') \
        .distinct()
    return reports


def return_symptom_list(user_id, date_updated, staff_id):
    """
    Returns a list of symptoms for the patient.
    @param user_id: the patient user id
    @param date_updated: date of the submitted symptom
    @param staff_id: the user id of the assigned staff
    @return: symptom list
    """
    criteria = Q(user_id=user_id) & Q(date_updated__date=date_updated) & Q(
        user__patients_assigned_flags__staff_id=staff_id)

    report_symptom_list = PatientSymptom.objects.select_related('symptom', 'user') \
        .filter(criteria) \
        .values('symptom_id', 'data', 'symptom__name', 'is_viewed', 'user__patients_assigned_flags__is_active',
                'user__patients_assigned_flags__staff_id', 'user__first_name', 'user__last_name')
    return report_symptom_list


def return_symptoms(user_id, staff_id):
    """
    Returns a list of symptoms the patient has.
    @param staff_id:
    @param user_id: the patient id
    @return: list of symptoms
    """
    criteria = Q(user_id=user_id) & Q(user__patients_assigned_flags__staff_id=staff_id)

    return_patient_symptoms = PatientSymptom.objects.select_related('symptom', 'user').filter(criteria) \
        .values('symptom_id', 'data', 'symptom__name', 'is_viewed', 'user__patients_assigned_flags__is_active',
                'user__patients_assigned_flags__staff_id',
                'user__first_name', 'user__last_name')
    return return_patient_symptoms


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
