from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


@login_required
@never_cache
def list_symptoms(request):
    return render(request, 'symptoms/list.html')


@login_required
@never_cache
def create(request):
    return render(request, 'symptoms/create.html')


@login_required
@never_cache
def userid(request):
    return render(request, 'symptoms/userid.html')
