import json

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from appointments.forms import AvailabilityForm
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

        if request.method == 'POST':
            availability_form = AvailabilityForm(request.POST)

            if availability_form.is_valid():

                # Get the selected week days from post request
                availability_days = availability_form.cleaned_data.get('availability_days')

                # Get the selected availability times from the post request
                availability_times = dict(availability_form.data.lists()).get('availability_select[]')

                times_list = []
                for time in availability_times:
                    times_list.append(json.loads(time))  # Process JSON

                # Need to convert from date to datetime object
                date_start = datetime.combine(availability_form.cleaned_data.get('start_date'), datetime.max.time())
                date_end = datetime.combine(availability_form.cleaned_data.get('end_date'), datetime.max.time())

                date_current = date_start

                while date_current <= date_end:
                    # Only add availabilities at the selected days of the week
                    if date_current.strftime("%A").lower() in availability_days:

                        for time in times_list:
                            # Creating datetime objects for the start and end times
                            start_datetime_object = datetime.strptime(
                                date_current.strftime('%Y/%m/%d ') + time.get('start'), '%Y/%m/%d %H:%M')
                            end_datetime_object = datetime.strptime(
                                date_current.strftime('%Y/%m/%d ') + time.get('end'), '%Y/%m/%d %H:%M')

                            # Fetch existing appointments at current date of the while loop
                            existing_appointments_at_current_date = list(Appointment.objects.filter(
                                start_date__year=date_current.year,
                                start_date__month=date_current.month,
                                start_date__day=date_current.day,
                                staff=request.user
                            ).values('start_date', 'end_date'))

                            # Check if availabilitiy collides with already existing appointment objects
                            for existing_appt in existing_appointments_at_current_date:
                                if existing_appt.get('start_date') < start_datetime_object < existing_appt.get(
                                        'end_date') or existing_appt.get(
                                    'start_date') < end_datetime_object < existing_appt.get('end_date'):
                                    # Don't create Appointment objects and display error message
                                    messages.error(request,
                                                   'The availability was not created. There already exists an appointment or availability between ' + start_datetime_object.strftime(
                                                       '%Y-%m-%d %H:%M') + ' and ' + end_datetime_object.strftime(
                                                       '%Y-%m-%d %H:%M'))
                                    return redirect('appointments:add_availabilities')

                            apt = Appointment.objects.create(staff=request.user, patient=None,
                                                             start_date=start_datetime_object,
                                                             end_date=end_datetime_object)
                            apt.save()

                    # Increment to next day
                    date_current += timedelta(days=1)

        else:
            availability_form = AvailabilityForm()

        return render(request, 'appointments/add_availabilities.html', {
            'availability_form': availability_form
        })


def list_availabilities(request):
    return render(request, 'appointments/availabilities.html')
