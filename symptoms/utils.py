from symptoms.models import PatientSymptom


# Input as [1] for symptom_id 1 or [1, 2] for multiple [#, #, ...]
def symptom_count_by_id(symptom_id_list):
    return PatientSymptom.objects.filter(symptom_id__in=symptom_id_list).count()
