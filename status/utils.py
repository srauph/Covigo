from django.db.models import Q

from symptoms.models import PatientSymptom


def return_reports(patient_ids, staff_id):
    criteria = Q(user_id__in=patient_ids) & Q(user__patients_assigned_flags__staff_id=staff_id)

    reports = PatientSymptom.objects.select_related('user').filter(criteria) \
        .values('date_updated__date', 'user_id', 'is_viewed', 'user__first_name', 'user__last_name',
                'user__patients_assigned_flags__is_active', 'user__patients_assigned_flags__staff_id') \
        .distinct()
    return reports


def return_symptom_list(user_id, date_updated, staff_id):
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
    patient_symptom = PatientSymptom.objects.all().filter(user_id=user_id, due_date__lte=date, data=None)
    return patient_symptom.exists()


def return_symptoms_for_today(user_id, date):
    return_patient_symptoms = PatientSymptom.objects.select_related('symptom', 'user') \
        .values('symptom_id', 'data', 'symptom__name', 'is_viewed', 'user__patients_assigned_flags__is_active',
                'user__first_name', 'user__last_name') \
        .filter(user_id=user_id, due_date=date)
    return return_patient_symptoms
