from django.db.models import Count
from symptoms.models import PatientSymptom


# Input as [1] for symptom_id 1 or [1, 2] for multiple [#, #, ...]
def symptom_count_by_id(symptom_id_list):
    if not isinstance(symptom_id_list, list):
        symptom_id_list = [symptom_id_list]

    results = PatientSymptom.objects \
        .filter(symptom_id__in=symptom_id_list) \
        .values('symptom_id') \
        .annotate(Count('symptom_id')) \
        .order_by('symptom_id__count')

    return results[0].get('symptom_id__count')
