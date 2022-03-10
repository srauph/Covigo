import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.datetime_safe import datetime
from django.views.decorators.cache import never_cache

from accounts.models import Patient, Flag
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
def patient_report_modal(request, user_id, date_updated):
    # When the view report button is pressed a POST request is made
    if request.method == "POST":
        # Ensure this was an ajax call
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':

            # Gets all symptoms' info required for the report
            report_symptom_list = PatientSymptom.objects.select_related('symptom', 'user') \
                .values('symptom_id', 'data', 'symptom__name', 'is_viewed', 'user__patients_assigned_flags__is_active',
                        'user__first_name', 'user__last_name') \
                .filter(user_id=user_id, date_updated=date_updated)

            # Check if the patient is flagged
            try:
                is_patient_flagged = Flag.objects.filter(patient_id=user_id).get(is_active=1)
            except Exception:
                is_patient_flagged = False

            # Ensure the report has not been viewed before
            if not report_symptom_list[0]['is_viewed']:
                # Set the report to viewed
                PatientSymptom.objects.filter(user_id=user_id, date_updated=date_updated).update(is_viewed=1)

            # Render as an httpResponse for the modal to use
            return HttpResponse(render_to_string('status/patient-report-modal.html', context={
                'user_id': user_id,
                'date': datetime.strptime(date_updated, '%Y-%m-%d %H:%M:%S.%f+00:00'),
                'report_symptom_list': report_symptom_list,
                'is_flagged': is_patient_flagged,
                'patient_name': report_symptom_list[0]['user__first_name'] + ' ' + report_symptom_list[0][
                    'user__last_name'],
            }, request=request))

    return HttpResponse("Invalid request.")


@login_required
@never_cache
def patient_reports_table(request):
    doctor = request.user

    # Get doctors patient's user id(s)
    patient_ids = []
    for users in Patient.objects.all():
        if users.staff_id == doctor.id:
            patient_ids.append(users.user_id)

    reports = PatientSymptom.objects.select_related('user') \
        .values('date_updated', 'user_id', 'is_viewed', 'user__first_name', 'user__last_name',
                'user__patients_assigned_flags__is_active') \
        .filter(user_id__in=patient_ids).distinct()

    serialized_reports = json.dumps({'data': list(reports)}, cls=DjangoJSONEncoder, default=str)

    return HttpResponse(serialized_reports, content_type='application/json')
