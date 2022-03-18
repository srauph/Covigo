import json

from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.datetime_safe import datetime
from django.views.decorators.cache import never_cache
import datetime
from accounts.models import Flag
from accounts.utils import get_assigned_staff_id_by_patient_id
from status.utils import return_reports, return_symptom_list, return_symptoms, check_report_exist
from symptoms.models import PatientSymptom


@login_required
@never_cache
def index(request):
    user = request.user
    if not user.is_staff:
        assigned_staff_id = get_assigned_staff_id_by_patient_id(user.id)

        patient_ids = [request.user.id]
        reports = return_reports(patient_ids, assigned_staff_id)
        patient_symptoms = return_symptoms(request.user.id, assigned_staff_id)
        report_exist = check_report_exist(request.user.id, datetime.datetime.now())
        return render(request, 'status/index.html', {
            'reports': reports,
            'symptoms': patient_symptoms,
            'report_exist': report_exist,
            'is_quarantining': request.user.patient.is_quarantining
        })
    raise Http404("The requested resource was not found on this server.")


@login_required
@never_cache
def patient_reports(request):
    doctor = request.user

    # Get doctors patient name(s) and user id(s)
    if doctor.has_perm('view_patientsymptom'):

        patient_ids = list(doctor.staff.get_assigned_patient_users().values_list("id", flat=True))

        # Return a QuerySet with all distinct reports from the doctors patients based on their updated date,
        # if it's viewed and if the patient is flagged
        reports = return_reports(patient_ids, request.user.id).order_by('is_viewed',
                                                                        '-user__patients_assigned_flags__is_active',
                                                                        '-date_updated').distinct()
        return render(request, 'status/patient-reports.html', {
            'patient_reports': reports
        })
    else:
        # TODO: this should change later, probably django has a method to redirect all unauthorized requests to a 401 page
        raise PermissionDenied


@login_required
@never_cache
def patient_reports_table(request):
    doctor = request.user

    patient_ids = list(doctor.staff.get_assigned_patient_users().values_list("id", flat=True))

    reports = return_reports(patient_ids, doctor.id)

    serialized_reports = json.dumps({'data': list(reports)}, cls=DjangoJSONEncoder, default=str)

    return HttpResponse(serialized_reports, content_type='application/json')


@login_required
@never_cache
def patient_report_modal(request, user_id, date_updated):
    # When the view report button is pressed a POST request is made
    if request.method == "POST":
        # Ensure this was an ajax call
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':

            # Get the assigned staff id for the patient
            if request.user.is_staff:  # Doctor is viewing
                staff_id = request.user.id
            else:  # Patient is viewing
                staff_id = get_assigned_staff_id_by_patient_id(request.user.id)

            # # Gets all symptoms' info required for the report
            report_symptom_list = return_symptom_list(user_id, date_updated, staff_id)

            # Check if the patient is flagged
            try:
                is_patient_flagged = Flag.objects.filter(patient_id=user_id).get(is_active=1)
            except Exception:
                is_patient_flagged = False
            #
            # # Ensure the report has not been viewed before
            if not report_symptom_list[0]['is_viewed']:
                # Set the report to viewed
                PatientSymptom.objects.filter(user_id=user_id, date_updated__date=date_updated).update(is_viewed=1)

            # Render as an httpResponse for the modal to use
            return HttpResponse(render_to_string('status/patient-report-modal.html', context={
                'user_id': user_id,
                'date': date_updated,
                'is_staff': request.user.is_staff,
                'is_flagged': is_patient_flagged,
                'patient_name': report_symptom_list[0]['user__first_name'] + ' ' + report_symptom_list[0][
                    'user__last_name'],
            }, request=request))

    return HttpResponse("Invalid request.")


@login_required
@never_cache
def patient_reports_modal_table(request, user_id, date_updated):
    # Get the assigned staff id for the patient
    if request.user.is_staff:  # Doctor is viewing
        staff_id = request.user.id
    else:  # Patient is viewing
        staff_id = get_assigned_staff_id_by_patient_id(request.user.id)

    # Return a query set of all symptoms for the patient
    report_symptom_list = return_symptom_list(user_id, date_updated, staff_id)

    # Serialize it in a JSON format for the datatable to parse
    serialized_reports = json.dumps({'data': list(report_symptom_list)}, cls=DjangoJSONEncoder, default=str)

    return HttpResponse(serialized_reports, content_type='application/json')


@login_required
@never_cache
def create_patient_report(request):
    current_user = request.user.id
    report = PatientSymptom.objects.filter(user_id=current_user, due_date__lte=datetime.datetime.now(), data=None)
    if request.method == 'POST':
        for r in report:
            report_data = request.POST.get('data')
            r.save(data=report_data)
    return render(request, 'status/create-status-report.html', {
        'report': report
    })
