from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


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
    return render(request, 'symptoms/create_symptom.html')


@login_required
@never_cache
def assign_symptom(request):
    return render(request, 'symptoms/assign_symptom.html')
