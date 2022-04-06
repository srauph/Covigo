from django.db.models import Count, Q, Max, Min
from django.utils.datetime_safe import datetime

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
    Assigns a symptom to a user with a by a specific due date, but will ignore already existing symptom ids.
    @param symptom_id: the symptom's id
    @param user_id: the user id being assigned a symptom
    @param due_date: due date of the symptom
    """
    query_list = []  # store the queries to be executed in bulk

    # Check if a record exists for the same symptom for a user with a specific due date
    query_filter = Q(symptom_id=symptom_id) & Q(user_id=user_id) & Q(due_date=due_date)
    if not PatientSymptom.objects.filter(query_filter).exists():  # ensure no record exists already
        patient_symptom = PatientSymptom(symptom_id=symptom_id, user_id=user_id, due_date=due_date)
        query_list.append(patient_symptom)

    # Only create the records if the list is not empty
    if query_list:
        PatientSymptom.objects.bulk_create(query_list)


def get_earliest_reporting_due_date(user_id):
    """
    Gets the earliest symptom report due date with data=None (null).
    @param user_id: user id
    @return: latest datetime if it exists otherwise None
    """
    try:
        return PatientSymptom.objects.filter(Q(user_id=user_id) & Q(data=None)).aggregate(Min('due_date'))[
            'due_date__min']
    except Exception:
        return None


def get_latest_reporting_due_date(user_id):
    """
    Gets the latest symptom report due date with data=None (null).
    @param user_id: user id
    @return: latest datetime if it exists otherwise None
    """
    try:
        return PatientSymptom.objects.filter(Q(user_id=user_id) & Q(data=None)).aggregate(Max('due_date'))[
            'due_date__max']
    except Exception:
        return None


def is_symptom_editing_allowed(user_id):
    """
    Checks if the doctor is allowed to edit a users symptoms.
    It ensures that there is an existing due date with data=null in the future.
    @param user_id: user id of the patient
    @return: true if allowed, false otherwise
    """
    latest_due_date = get_latest_reporting_due_date(user_id)
    if latest_due_date is None:
        return False
    else:
        return datetime.now() < latest_due_date


def get_assigned_symptoms_from_patient(patient):
    """
    Checks if editing symptoms is allowed and returns the assigned symptoms with data = None meaning they still have to report them.
    Returns () if there is no symptom to report meaning they have expired or there are no new reports.
    @param patient: the patient user
    @return: symptoms if they must still be reported otherwise ()
    """
    if is_symptom_editing_allowed(patient.id):
        return patient.symptoms.all().filter(patient_symptoms__data=None)
    else:
        return ()
