import json
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from accounts.models import Staff
from accounts.utils import get_assigned_staff_id_by_patient_id, get_users_names, get_is_staff
from appointments.forms import AvailabilityForm
from datetime import datetime, timedelta
from appointments.models import Appointment


@login_required
@never_cache
def index(request):
    staff_id = get_assigned_staff_id_by_patient_id(request.user.id)
    booked_appointments = Appointment.objects.filter(patient=request.user.id, staff=staff_id)
    is_staff = get_is_staff(request.user.id)

    return render(request, 'appointments/index.html', {
        'booked_appointments': booked_appointments,
        'is_staff': is_staff
    })


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

                            # Check if availability collides with already existing appointment objects
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

                            # Get user's Staff Id:
                            staff_id = Staff.objects.filter(user=request.user).first().id

                            # Create new Appointment object
                            apt = Appointment.objects.create(staff_id=staff_id, patient=None,
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


@login_required
@never_cache
def book_appointments(request):
    staff_id = get_assigned_staff_id_by_patient_id(request.user.id)
    staff_user_id = Staff.objects.get(id=staff_id).user_id
    staff_name = get_users_names(staff_user_id)

    print(staff_id, staff_user_id, staff_name)

    if request.method == 'POST' and request.POST.get('Book Appointment'):
        booking_id = request.POST.get('Book Appointment')

        # books a single appointment by adding the patient's id to the appointment's patient_id column
        booking = Appointment.objects.get(id=booking_id)
        booking.patient = request.user
        booking.save()

        # success message to show user
        messages.success(request, 'The appointment was booked successfully.')
        return redirect('appointments:book_appointments')

    if request.method == 'POST' and request.POST.get('Book Selected Appointments'):
        booking_ids = request.POST.getlist('booking_ids[]')

        # books all selected appointments by adding the patient's id to the appointment's patient_id column
        for booking_id in booking_ids:
            booking = Appointment.objects.get(id=booking_id)
            booking.patient = request.user
            booking.save()

        # success message to show user if appointments were booked
        if len(booking_ids) > 0:
            messages.success(request, 'The selected appointments were booked successfully.')
            return redirect('appointments:index')

    return render(request, 'appointments/book_appointments.html', {
        'appointments': Appointment.objects.filter(patient=None, staff=staff_id).all(),
        'staff_name': staff_name
    })


@login_required
@never_cache
def cancel_or_delete_appointments_or_availabilities(request):
    if request.user.is_staff:
        logged_in_filter = Q(patient_id__isnull=False, staff_id=request.user.staff.id)

    else:
        logged_in_filter = Q(patient_id=request.user.id)

    if request.method == 'POST' and request.POST.get('Cancel Appointment'):
        booked_id = request.POST.get('Cancel Appointment')

        # cancels a single appointment by setting the patient's id in the appointment's patient_id column to "None"
        booked = Appointment.objects.get(id=booked_id)
        booked.patient = None
        booked.save()
        return redirect('appointments:cancel_or_delete_appointments_or_availabilities')

    if request.method == 'POST' and request.POST.get('Cancel Selected Appointments'):
        booked_ids = request.POST.getlist('booked_ids[]')

        # cancels all selected appointments by setting the patient's id in the appointment's patient_id column to "None"
        for booked_id in booked_ids:
            booked = Appointment.objects.get(id=booked_id)
            booked.patient = None
            booked.save()
        return redirect('appointments:index')

    return render(request, 'appointments/cancel_appointments.html', {
        'appointments': Appointment.objects.filter(logged_in_filter).all()
    })
