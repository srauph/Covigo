from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from symptoms.models import Symptom, PatientSymptom
from symptoms.forms import CreateSymptomForm


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
                    return redirect('symptoms:list_symptoms')

                else:
                    return render(request, 'symptoms/create_symptom.html', {
                        'form': create_symptom_form
                    })

            else:
                create_symptom_form.add_error('name', "This symptom name already exists for a given symptom.")

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

        if symptom.name == edit_symptom_form.data.get('name') and symptom.description == edit_symptom_form.data.get(
                'description'):
            edit_symptom_form.add_error(None,
                                        "No edits made on this symptom. If you wish to make no changes, please click the \"Cancel\" button to go back to the list of symptoms.")

        if edit_symptom_form.is_valid():
            edit_symptom_form.save()

            if request.POST.get('Edit and Return'):
                return redirect('symptoms:list_symptoms')

            else:
                return render(request, 'symptoms/edit_symptom.html', {
                    'form': edit_symptom_form
                })

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

    if request.method == 'POST':

        for symptom_id in request.POST.getlist('symptom'):
            filter1 = Q(symptom_id=symptom_id) & Q(user_id=patient.id)
            # to not override the existing patient_symptom instance, will make it more robust in next sprints
            if not PatientSymptom.objects.filter(filter1):
                patient_symptom = PatientSymptom(symptom_id=symptom_id, user_id=patient.id)
                patient_symptom.save()
            # TODO: we need to discuss the edit feature and the case when a doctor wants to remove a symptom from a patient.

        quarantine_status_changed = request.POST.get('should_quarantine') is not None
        if patient_information.is_quarantining is not quarantine_status_changed:
            patient_information.is_quarantining = quarantine_status_changed
            patient_information.save()

        return redirect('accounts:list_users')

    return render(request, 'symptoms/assign_symptom.html', {
        'symptoms': Symptom.objects.all(),
        'assigned_symptoms': assigned_symptoms,
        'patient': patient,
        'patient_name': patient_name,
        'patient_is_quarantining': patient_information.is_quarantining,
    })


@login_required
@never_cache
def toggle_symptom(request, symptom_id):
    symptom = Symptom.objects.get(id=symptom_id)
    symptom.is_active = not symptom.is_active
    symptom.save()

    return redirect('symptoms:list_symptoms')
