from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from symptoms.models import Symptom
from .forms import CreateSymptomForm


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
        form = CreateSymptomForm(request.POST)

        if form.is_valid():
            form.save()

            if request.POST.get('Submit and return'):
                return redirect('symptoms:list_symptoms')

            else:
                return render(request, 'symptoms/create_symptom.html', {
                    'form': form
                })

    else:
        form = CreateSymptomForm()

    return render(request, 'symptoms/create_symptom.html', {
        'form': form
    })


@login_required
@never_cache
def edit_symptom(request, symptom_id):
    symptom = Symptom.objects.get(id=symptom_id)

    if request.method == 'POST':
        form = CreateSymptomForm(request.POST, instance=symptom)

        if form.is_valid():
            form.save()

            if request.POST.get('Submit and return'):
                return redirect('symptoms:list_symptoms')

            else:
                return render(request, 'symptoms/edit_symptom.html', {
                    'form': form
                })

    else:
        form = CreateSymptomForm(instance=symptom)

    return render(request, 'symptoms/edit_symptom.html', {
        'form': form
    })


@login_required
@never_cache
def assign_symptom(request):
    return render(request, 'symptoms/assign_symptom.html')
