from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def list_symptoms(request):
    return render(request, 'symptoms/list.html')


@never_cache
def create(request):
    return render(request, 'symptoms/create.html')


@never_cache
def userid(request):
    return render(request, 'symptoms/userid.html')
