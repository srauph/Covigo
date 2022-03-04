from django.contrib.auth.models import User
from django.db.models import Max, Count
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.cache import never_cache

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
