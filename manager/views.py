from django.contrib.auth.models import User
from django.shortcuts import render

from accounts.models import Patient, Staff


def index(request):
    user_count = User.objects.count()
    patient_count = Patient.objects.count()
    staff_count = Staff.objects.count()
    return render(request, 'manager/index.html', {
        "user_count": user_count,
        "patient_count": patient_count,
        "staff_count": staff_count,
    })


def contact_tracing(request):
    user_count = User.objects.count()
    return render(request, 'manager/contact_tracing.html', {"user_count": user_count})
