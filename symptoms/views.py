from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from symptoms.models import Symptom


@login_required
@never_cache
def index(request):
    return redirect('symptoms:list_symptoms')


@login_required
@never_cache
def list_symptoms(request):
    return render(request, 'symptoms/list_symptoms.html')


@login_required
@never_cache
def create_symptom(request):
    if request.method == 'POST':
        symptom = Symptom()
        symptom.name = request.POST.get('symptom_name')
        symptom.description = request.POST.get('symptom_description')
        symptom.save()

        if request.POST.get('submit_and_return'):
            return redirect('symptoms:list_symptoms')

        else:
            return render(request, 'symptoms/create_symptom.html', {
                'previous_symptom': symptom
            })

    else:
        return render(request, 'symptoms/create_symptom.html')


@login_required
@never_cache
def assign_symptom(request):
    return render(request, 'symptoms/assign_symptom.html')
