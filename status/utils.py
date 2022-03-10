from symptoms.models import PatientSymptom


def return_reports(patient_ids):
    reports = PatientSymptom.objects.select_related('user') \
        .values('date_updated', 'user_id', 'is_viewed', 'user__first_name', 'user__last_name',
                'user__patients_assigned_flags__is_active') \
        .filter(user_id__in=patient_ids).distinct()
    return reports
