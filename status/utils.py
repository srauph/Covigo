from symptoms.models import PatientSymptom


def return_reports(patient_ids):
    reports = PatientSymptom.objects.select_related('user') \
        .values('date_updated__date','user_id', 'is_viewed', 'user__first_name', 'user__last_name',
                'user__patients_assigned_flags__is_active') \
        .filter(user_id__in=patient_ids).distinct()
    return reports


def return_symptom_list(user_id, date_updated):
    report_symptom_list = PatientSymptom.objects.select_related('symptom', 'user') \
        .values('symptom_id', 'data', 'symptom__name', 'is_viewed', 'user__patients_assigned_flags__is_active',
                'user__first_name', 'user__last_name') \
        .filter(user_id=user_id, date_updated__date=date_updated)
    return report_symptom_list
