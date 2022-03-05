from django.contrib.auth.models import User
from django.db.models import Max, Count
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.generic import UpdateView

from accounts.models import Patient, Staff
from symptoms.models import PatientSymptom


@login_required
@never_cache
def index(request):
    return render(request, 'status/index.html')


@login_required
@never_cache
def patient_reports(request):
    doctor = request.user

    # Get doctors patient name(s) and user id(s)
    patient_ids = []
    for users in Patient.objects.all():
        if users.staff_id == doctor.id:
            patient_ids.append(users.user_id)

    # Return a QuerySet with all distinct reports from the doctors patients based on their updated date,
    # if it's viewed and if the patient is flagged
    # TODO see if any edge cases exists that break it
    reports = PatientSymptom.objects.select_related('user') \
        .values('date_updated', 'user_id', 'is_viewed', 'user__first_name', 'user__last_name',
                'user__patients_assigned_flags__is_active') \
        .filter(user_id__in=patient_ids).order_by('is_viewed', '-user__patients_assigned_flags__is_active',
                                                  '-date_updated').distinct()

    return render(request, 'status/patient-reports.html', {
        'patient_reports': reports
    })


@login_required
@never_cache
def patient_report_modal(request):  # , user_id, date_updated):

    reports = PatientSymptom.objects.select_related('user') \
        .values('date_updated', 'user_id', 'is_viewed', 'user__first_name', 'user__last_name',
                'user__patients_assigned_flags__is_active') \
        .filter(user_id__in=[3]).order_by('is_viewed', '-user__patients_assigned_flags__is_active',
                                          '-date_updated').distinct()
    user_id = reports[0]['user_id']
    date_updated = reports[0]['date_updated']

    ################################################

    report_symptom_list = PatientSymptom.objects.select_related('symptom').values('symptom_id', 'data',
                                                                                  'symptom__name').filter(
        user_id=user_id,
        date_updated=date_updated)

    #print(report_symptom_list.query)
    #print(report_symptom_list)
    return render(request, 'status/patient-report-modal.html', {
        'report_symptom_list': report_symptom_list
    })
