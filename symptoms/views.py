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


@login_required
@never_cache
def list_symptoms(request):
    return render(request, 'symptoms/list_symptoms.html', {
        'symptoms': Symptom.objects.all()
    })


@login_required
@never_cache
def create_symptom(request):
    if request.method == 'POST':
        create_symptom_form = CreateSymptomForm(request.POST)

        if create_symptom_form.is_valid():
            if not Symptom.objects.filter(name=create_symptom_form.data.get('name')).exists():
                create_symptom_form.save()

                if request.POST.get('Submit and return'):
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


@login_required
@never_cache
def edit_symptom(request, symptom_id):
    symptom = Symptom.objects.get(id=symptom_id)

    if request.method == 'POST':
        edit_symptom_form = CreateSymptomForm(request.POST, instance=symptom)

        if edit_symptom_form.is_valid():
            edit_symptom_form.save()

            if request.POST.get('Update and return'):
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

    if request.method == 'POST':

        for symptom_id in request.POST.getlist('symptom'):
            filter1 = Q(symptom_id=symptom_id) & Q(user_id=patient.id)
            # to not override the existing patient_symptom instance, will make it more robust in next srpints
            if not PatientSymptom.objects.filter(filter1):
                patient_symptom = PatientSymptom(symptom_id=symptom_id, user_id=patient.id)
                patient_symptom.save()
            # TODO: we need to discuss the edit feature and the case when a doctor wants to remove a symptom from a patient.
        return redirect('accounts:list_users')

    return render(request, 'symptoms/assign_symptom.html', {
        'symptoms': Symptom.objects.all(),
        'assigned_symptoms': assigned_symptoms,
        'patient': patient,
        'patient_name': patient_name
    })


@login_required
@never_cache
def toggle_symptom(request, symptom_id):
    symptom = Symptom.objects.get(id=symptom_id)
    symptom.is_active = not symptom.is_active
    symptom.save()

    return redirect('symptoms:list_symptoms')
