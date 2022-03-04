from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from appointments.forms import AvailabilitySlotForm
from accounts.models import Staff


@login_required
@never_cache
def index(request):
    return render(request, 'appointments/index.html')


@login_required
@never_cache
def edit_availabilities(request):
    if request.user.is_staff:

        if request.POST:
            availability_slot_form = AvailabilitySlotForm(request.POST)

            if availability_slot_form.is_valid():
                print(availability_slot_form.data)

                availability_slot_minutes = int(availability_slot_form.data.get('availability_slot_time'))
                availability_advance = int(availability_slot_form.data.get('availability_advance'))

                availability_slot_generator = (availability_advance * 10000) + availability_slot_minutes

                stf = Staff.objects.filter(user_id=request.user.id).get()

                if stf:
                    stf.availability_slot_generator = availability_slot_generator
                    stf.save()

        return render(request, 'appointments/edit_availabilities.html', {
            'form': AvailabilitySlotForm()
        })
