import json
from django.forms import formset_factory
from django.shortcuts import render
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

                availability_days = availability_form.cleaned_data.get('availability_days')

                availability_times = dict(availability_form.data.lists()).get('availability_select[]')

                times_list = []
                for time in availability_times:
                    x = json.loads(time)
                    times_list.append(x)

                # Need to convert from date to datetime object
                date_start = datetime.combine(availability_form.cleaned_data.get('end_date'), datetime.max.time())
                date_end = datetime.combine(availability_form.cleaned_data.get('end_date'), datetime.max.time())

                date_current = date_start

                while date_current <= date_end:
                    # Only add availabilities at the selected days of the week
                    if date_current.strftime("%A").lower() in availability_days:

                        for time in times_list:
                            start_datetime_object = datetime.strptime(
                                date_current.strftime('%Y/%m/%d ') + time.get('start'), '%Y/%m/%d %H:%M')
                            end_datetime_object = datetime.strptime(
                                date_current.strftime('%Y/%m/%d ') + time.get('end'), '%Y/%m/%d %H:%M')

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
