from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from symptoms.models import Symptom, PatientSymptom
from symptoms.forms import CreateSymptomForm
from django.contrib import messages

from symptoms.utils import assign_symptom_to_user, get_remaining_start_end_due_dates


@login_required
@never_cache
def index(request):
    return redirect('symptoms:list_symptoms')


# this function simply renders the "Symptoms" list page with all
# the symptoms present in the database along with their respective details
@login_required
@never_cache
def list_symptoms(request):
    return render(request, 'symptoms/list_symptoms.html', {
        'symptoms': Symptom.objects.all()
    })


# this function allows form data from the "Create Symptom" page to be submitted and handled properly
# in such a manner as to dynamically change the view depending on what request method is detected and used
@login_required
@never_cache
def create_symptom(request):
    if request.method == 'POST':
        create_symptom_form = CreateSymptomForm(request.POST)

        if create_symptom_form.is_valid():
            if not Symptom.objects.filter(name=create_symptom_form.data.get('name')).exists():
                create_symptom_form.save()

                if request.POST.get('Create and Return'):
                    messages.success(request, 'The symptom was created successfully.')
                    return redirect('symptoms:list_symptoms')

                else:
                    messages.success(request, 'The symptom was created successfully.')
                    return render(request, 'symptoms/create_symptom.html', {
                        'form': create_symptom_form
                    })

            else:
                messages.error(request,
                               'The symptom was not created successfully: This symptom name already exists for a given symptom. Please change the symptom name.')

    else:
        create_symptom_form = CreateSymptomForm()

    return render(request, 'symptoms/create_symptom.html', {
        'form': create_symptom_form
    })


# this function allows form data from the "Edit Symptom" page to be submitted and handled properly
# in such a manner as to dynamically change the database symptom contents, depending on what request
# method is detected and used, by making edits to it
@login_required
@never_cache
def edit_symptom(request, symptom_id):
    symptom = Symptom.objects.get(id=symptom_id)

    if request.method == 'POST':
        edit_symptom_form = CreateSymptomForm(request.POST, instance=symptom)

        # TODO: See what happened here (old code from merge conflict)
        # if symptom.name == edit_symptom_form.data.get('name') and symptom.description == edit_symptom_form.data.get(
        #         'description'):
        #     edit_symptom_form.add_error(None,
        #                                 "No edits made on this symptom. If you wish to make no changes, please click the \"Cancel\" button to go back to the list of symptoms.")

        if not edit_symptom_form.has_changed():
            messages.error(request,
                           "The symptom was not edited successfully: No edits made on this symptom. If you wish to make no changes, please click the \"Cancel\" button to go back to the list of symptoms.")
            return render(request, 'symptoms/edit_symptom.html', {
                'form': edit_symptom_form
            })

        if edit_symptom_form.is_valid():
            if not Symptom.objects.filter(name=edit_symptom_form.data.get('name')).exists():
                edit_symptom_form.save()

                if request.POST.get('Edit and Return'):
                    messages.success(request, 'The symptom was edited successfully.')
                    return redirect('symptoms:list_symptoms')

            else:
                messages.error(request,
                               'The symptom was not edited successfully: This symptom name already exists for a given symptom. Please change the symptom name.')

    else:
        edit_symptom_form = CreateSymptomForm(instance=symptom)

    return render(request, 'symptoms/edit_symptom.html', {
        'form': edit_symptom_form
    })


@login_required
@never_cache
def assign_symptom(request, user_id):
    patient = User.objects.get(pk=user_id)
    if patient.first_name == "" and patient.last_name == "":
        patient_name = patient
    else:
        patient_name = f"{patient.first_name} {patient.last_name}"
    assigned_symptoms = patient.symptoms.all()
    patient_information = patient.patient

    # Ensure this is a post request
    if request.method == 'POST':

        # Get the action of the button
        action = str(request.POST.get('button-action'))

        # Ensure this was the action of assigning symptoms
        if action == 'assign':
            # Assigns symptoms selected for patient
            date = datetime.strptime(request.POST['starting_date'], '%Y-%m-%dT%H:%M')

            interval = int(request.POST.get('interval'))
            while interval != 0:
                for symptom_id in request.POST.getlist('symptom'):
                    assign_symptom_to_user(symptom_id, user_id, date)
                interval = interval - 1
                date = date + timedelta(days=1)

            # Assigns quarantine status for patient
            quarantine_status_changed = request.POST.get('should_quarantine') is not None
            if patient_information.is_quarantining is not quarantine_status_changed:
                patient_information.is_quarantining = quarantine_status_changed
                patient_information.save()
        else:
            if action == 'update':

                # TODO remove ' '
                updated_symptom_list: list = request.POST.getlist('symptom')
                earliest_due_date, latest_due_date = get_remaining_start_end_due_dates(user_id)

                # Assigned new symptoms
                # TODO merge duplicate code with the assign one
                if latest_due_date is not None:
                    interval = (latest_due_date.day - earliest_due_date.day) + 1
                    due_date = latest_due_date.replace(day=earliest_due_date.day)

                    while interval != 0:
                        for symptom_id in updated_symptom_list:
                            assign_symptom_to_user(symptom_id, user_id, due_date)
                        interval = interval - 1
                        due_date = due_date + timedelta(days=1)
                    print("it's not none")
                else:
                    print("it's none")

                # delete old symptoms with data=null

        return redirect('accounts:list_users')

    return render(request, 'symptoms/assign_symptom.html', {
        'symptoms': Symptom.objects.all(),
        'assigned_symptoms': assigned_symptoms,
        'patient': patient,
        'patient_name': patient_name,
        'patient_is_quarantining': patient_information.is_quarantining,
        # TODO real method
        'allow_editing': True,
    })


@login_required
@never_cache
def toggle_symptom(request, symptom_id):
    symptom = Symptom.objects.get(id=symptom_id)
    symptom.is_active = not symptom.is_active
    symptom.save()

    return redirect('symptoms:list_symptoms')
