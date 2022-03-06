from django.forms import formset_factory
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from appointments.forms import AvailabilityForm, TimeForm, BaseTimeFormSet
from accounts.models import Staff


@login_required
@never_cache
def index(request):
    return render(request, 'appointments/index.html')


@login_required
@never_cache
def add_availabilities(request):
    if request.user.is_staff:

        TimeFormSet = formset_factory(TimeForm, formset=BaseTimeFormSet)

        if request.method == 'POST':
            availability_form = AvailabilityForm(request.POST)
            time_formset = TimeFormSet(request.POST)

            if availability_form.is_valid() and time_formset.is_valid():

                print(availability_form.cleaned_data.get('availability_days'))
                print(availability_form.cleaned_data.get('slot_duration_hours'))
                print(availability_form.cleaned_data.get('slot_duration_minutes'))

                for time_form in time_formset:
                    print('start time: ', time_form.cleaned_data.get('start_time_hour'), ':', time_form.cleaned_data.get('start_time_minute'))
        else:
            availability_form = AvailabilityForm()
            time_formset = TimeFormSet()


        return render(request, 'appointments/add_availabilities.html', {
            'availability_form': availability_form,
            'time_formset': time_formset
        })
