from django.db.models import Count, Q, Max, Min

from symptoms.models import PatientSymptom


def symptom_count_by_id(symptom_id_list):
    """
    Gets the symptom count based on the symptom ids.
    i.e Input as [1] for symptom_id 1 or [1, 2] for multiple [#, #, ...]
    @param symptom_id_list: list of symptom ids
    @return: symptom count based on the symptom ids
    """
    if not isinstance(symptom_id_list, list):
        symptom_id_list = [symptom_id_list]

    results = PatientSymptom.objects \
        .filter(symptom_id__in=symptom_id_list) \
        .values('symptom_id') \
        .annotate(Count('symptom_id')) \
        .order_by('symptom_id__count')

    return results[0].get('symptom_id__count')


def assign_symptom_to_user(symptom_id, user_id, due_date):
    """
    Assigns a symptom to a user with a by a specific due date,but will ignore already existing symptom ids.
    @param symptom_id: the symptom's id
    @param user_id: the user id being assigned a symptom
    @param due_date: due date of the symptom
    """
    filter1 = Q(symptom_id=symptom_id) & Q(user_id=user_id) & Q(due_date=due_date)
    # to not override the existing patient_symptom instance, will make it more robust in next sprints
    if not PatientSymptom.objects.filter(filter1).exists():
        patient_symptom = PatientSymptom(symptom_id=symptom_id, user_id=user_id, due_date=due_date)
        patient_symptom.save()


def get_latest_symptom_due_date(user_id):
    """
    Gets the latest symptom due date a patient must report by.
    @param user_id: user id
    @return: latest datetime if it exists otherwise None
    """
    try:
        return PatientSymptom.objects.filter(Q(user_id=user_id) & Q(data=None)).aggregate(Max('due_date'))[
            'due_date__max']
    except Exception:
        return None


def get_earliest_symptom_due_date(user_id):
    """
    Gets the earliest symptom is due by.
    @param user_id: user id
    @return: earliest datetime if it exists otherwise None
    """
    try:
        return PatientSymptom.objects.filter(Q(user_id=user_id) & Q(data=None)).aggregate(Min('due_date'))[
            'due_date__min']
    except Exception:
        return None
