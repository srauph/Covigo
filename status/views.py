import json

from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.datetime_safe import datetime
from django.views.decorators.cache import never_cache
import datetime
from accounts.models import Flag
from accounts.utils import get_assigned_staff_id_by_patient_id
from status.utils import return_symptoms_for_today, get_reports_by_patient, get_patient_report_information, \
    get_reports_for_doctor
from symptoms.models import PatientSymptom


@login_required
@never_cache
def index(request):
    """
    The view of the index (Health Status) page for the status application.
    Returns
    @param request: http request from the client
    @return: status index page or 404 if user is not a staff
    """
    user = request.user
    if not user.is_staff:
        # Assigned staff user id for the viewing user
        assigned_staff_id = get_assigned_staff_id_by_patient_id(user.id)

        # Reports for the user
        reports = get_reports_by_patient(request.user.id)

        # Symptoms to report
        patient_symptoms = return_symptoms_for_today(request.user.id)

        return render(request, 'status/index.html', {
            'reports': reports,
            'symptoms': patient_symptoms,
            'is_reporting_today': patient_symptoms.exists(),
            'is_quarantining': request.user.patient.is_quarantining
        })
    raise Http404("The requested resource was not found on this server.")


@login_required
@never_cache
def patient_reports(request):
    """
    The view of the patient report page.
    @param request: http request from the client
    @return: patient report page
    """
    doctor = request.user

    # Get doctors patient name(s) and user id(s)
    if doctor.has_perm('symptoms.view_patientsymptom'):

        # list of patient ids for the doctor
        patient_ids = list(doctor.staff.get_assigned_patient_users().values_list("id", flat=True))

        # Return a QuerySet with all distinct reports from the doctors patients based on their updated date,
        # if it's viewed and if the patient is flagged
        reports = get_reports_for_doctor(patient_ids)

        return render(request, 'status/patient-reports.html', {
            'patient_reports': reports
        })
    else:
        # TODO: this should change later, probably django has a method to redirect all unauthorized requests to a 401 page
        raise PermissionDenied


@login_required
@never_cache
def patient_reports_table(request):
    """
    The view for the patient report table in json format.
    @param request: http request from the client
    @return: json of the report data
    """
    doctor = request.user

    # list of patient ids for the doctor
    patient_ids = list(doctor.staff.get_assigned_patient_users().values_list("id", flat=True))

    # Return a query set of reports for the patient for their assigned doctor
    reports = get_reports_for_doctor(patient_ids)

    # Serialize it in a JSON format for the datatable to parse
    serialized_reports = json.dumps({'data': list(reports)}, cls=DjangoJSONEncoder, default=str)

    return HttpResponse(serialized_reports, content_type='application/json')


@login_required
@never_cache
def patient_report_modal(request, user_id, date_updated):
    """
    The view of the patient report modal.
    @param request: http request from the client
    @param user_id: user id of the patient
    @param date_updated: date of the report
    @return: patient report modal page if post request otherwise an invalid request
    """
    # When the view report button is pressed a POST request is made
    if request.method == "POST":
        # Ensure this was an ajax call
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':

            # Gets all symptoms' info required for the report
            report_symptom_list = get_patient_report_information(user_id, date_updated)

            # Check if the patient is flagged
            try:
                is_patient_flagged = Flag.objects.filter(patient_id=user_id).get(is_active=1)
            except Exception:
                is_patient_flagged = False

            # Ensure the report has not been viewed before
            if not report_symptom_list[0]['is_viewed']:
                # Set the report to viewed
                PatientSymptom.objects.filter(
                    Q(user_id=user_id) & Q(date_updated__date=date_updated) & ~Q(data=None)).update(is_viewed=1)

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
    """
    The view of the patient report modal
    @param request: http request from the client
    @param user_id: user id of the patient
    @param date_updated: date of the report
    @return: json response of the report
    """
    # Return a query set of all symptoms for the patient
    report_symptom_list = get_patient_report_information(user_id, date_updated)

    # Serialize it in a JSON format for the datatable to parse
    serialized_reports = json.dumps({'data': list(report_symptom_list)}, cls=DjangoJSONEncoder, default=str)

    return HttpResponse(serialized_reports, content_type='application/json')


@login_required
@never_cache
def create_patient_report(request):
    """
    The view of creating a patient report.
    @param request: http request from the client
    @return: create-status-report page
    """
    current_user = request.user.id
    report = PatientSymptom.objects.filter(user_id=current_user, due_date__date__lte=datetime.datetime.now(), data=None)

    # Ensure it was a post request

    current_user = request.user.id
    report = PatientSymptom.objects.filter(user_id=current_user, due_date__date__lte=datetime.datetime.now())

    # Ensure it was a post request

    if request.method == 'POST':
        report_data = request.POST.getlist('data[id][]')
        data = request.POST.getlist('data[data][]')
        i = 0
        for s in report_data:
            symptom = PatientSymptom.objects.filter(id=int(s)).get()
            symptom.data = data[i]
            symptom.save()
            i = i + 1

        return redirect('status:index')
    return render(request, 'status/create-status-report.html', {
        'report': report
    })


@login_required
@never_cache
def edit_patient_report(request):
    """
        The view of editing a patient report.
        @param request: http request from the client
        @return: edit-status-report page
        """
    current_user = request.user.id
    report = PatientSymptom.objects.filter(user_id=current_user, due_date__date__lte=datetime.datetime.now())

    # Ensure it was a post request

    if request.method == 'POST':
        report_data = request.POST.getlist('data[id][]')
        data = request.POST.getlist('data[data][]')
        i = 0
        for s in report_data:
            symptom = PatientSymptom.objects.filter(id=int(s)).get()
            # check if user updated the symptom
            if data[i] != '':
                new_symptom = symptom
                new_symptom.is_hidden = True
                new_symptom.save()
                new_symptom.pk = None
                new_symptom.is_hidden = False
                new_symptom.data = data[i]
                new_symptom._state.adding = True
                new_symptom.save()
            i = i + 1

        return redirect('status:index')

    return render(request, 'status/edit-status-report.html', {
        'report': report
    })


def resubmit_request(request, patient_symptom_id):
    symptom = PatientSymptom.objects.filter(id=int(patient_symptom_id)).get()
    new_symptom = symptom
    new_symptom.is_hidden = True
    new_symptom.save()
    new_symptom.pk = None
    new_symptom.is_hidden = False
    new_symptom.data = None
    new_symptom._state.adding = True
    new_symptom.save()
    return redirect('status:patient-reports')
