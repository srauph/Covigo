from django.forms import formset_factory
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from appointments.forms import AvailabilityForm, TimeForm, BaseTimeFormSet
from datetime import datetime, timedelta
from appointments.models import Appointment


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

                availability_days = availability_form.cleaned_data.get('availability_days')

                slot_duration_in_minutes = int(availability_form.cleaned_data.get('slot_duration_hours')) * 60 + \
                                           int(availability_form.cleaned_data.get('slot_duration_minutes'))

                date_current = datetime.now()
                # Need to convert from date to datetime object
                date_until = datetime.combine(availability_form.cleaned_data.get('date_until'), datetime.max.time())

                while date_current <= date_until:
                    # Only add availabilities at the selected days of the week
                    if date_current.strftime("%A").lower() in availability_days:

                        # Process each availability time range
                        for time_form in time_formset:
                            start = datetime(date_current.year, date_current.month, date_current.day,
                                             time_form.cleaned_data.get('start_time_hour'),
                                             time_form.cleaned_data.get('start_time_minute'))
                            end = datetime(date_current.year, date_current.month, date_current.day,
                                           time_form.cleaned_data.get('end_time_hour'),
                                           time_form.cleaned_data.get('end_time_minute'))

                            while start < end:
                                # Create the individual Appointment objects between each time range with the slot
                                # duration
                                next_end = start + timedelta(minutes=slot_duration_in_minutes)
                                apt = Appointment.objects.create(staff=request.user, patient=None, start_date=start,
                                                                 end_date=next_end)
                                apt.save()
                                start = next_end
                    # Increment to next day
                    date_current += timedelta(days=1)

        else:
            availability_form = AvailabilityForm()
            time_formset = TimeFormSet()

        return render(request, 'appointments/add_availabilities.html', {
            'availability_form': availability_form,
            'time_formset': time_formset
        })
