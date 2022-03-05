from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from appointments.forms import AvailabilityForm
from accounts.models import Staff


@login_required
@never_cache
def index(request):
    return render(request, 'appointments/index.html')


@login_required
@never_cache
def add_availabilities(request):
    if request.user.is_staff:

        return render(request, 'appointments/add_availabilities.html', {
            'form': AvailabilityForm()
        })
