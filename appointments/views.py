import json
from django.contrib import messages
from django.contrib.auth.models import User
from django.core import serializers
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from accounts.models import Staff
from accounts.utils import get_assigned_staff_id_by_patient_id, get_users_names, get_is_staff
from appointments.forms import AvailabilityForm
from datetime import datetime, timedelta
from appointments.models import Appointment
from appointments.utils import cancel_appointments, delete_availabilities,  book_appointment


@login_required
@never_cache
def index(request):
    is_staff = get_is_staff(request.user.id)
    patient_booked_appointments = []
    doctor_booked_appointments_patient_name_dict = {}

    if not is_staff:
        assigned_staff_id = get_assigned_staff_id_by_patient_id(request.user.id)
        patient_booked_appointments = Appointment.objects.filter(patient=request.user.id, staff=assigned_staff_id).all()
    else:
        signed_in_staff_id = Staff.objects.get(user_id=request.user.id).id
        doctor_booked_appointments = Appointment.objects.filter(patient__isnull=False, staff=signed_in_staff_id).all()
        for appointment in doctor_booked_appointments:
            doctor_booked_appointments_patient_name_dict[appointment] = get_users_names(appointment.patient.id)

    return render(request, 'appointments/index.html', {
        'patient_booked_appointments': patient_booked_appointments,
        'doctor_booked_appointments_patient_name_dict': doctor_booked_appointments_patient_name_dict,
        'is_staff': is_staff
    })


@login_required
@never_cache
def add_availabilities(request):
    """
        This function handles the creation of availabilities (Appointment objects with patient_id=null).
        Before creating the availabilities, it checks if Appointment objects already exist at the specified time slots.
        :param request: the type of request that is processed in the "add_availabilities.html" template page
        :return: returns the specific template that is either rendered or redirected to based on the user input logic
        (either redirected to the "index.html" template page or rendered back to the default "add_availabilities.html" template page)
    """
    # Only staff can create availabilities for patients to book
    if request.user.is_staff:

        if request.method == 'POST':
            availability_form = AvailabilityForm(request.POST)

            if availability_form.is_valid():

                # Get the selected week days from post request
                availability_days = availability_form.cleaned_data.get('availability_days')

                # Get the selected availability times from the post request
                availability_times = dict(availability_form.data.lists()).get('availability_select[]')

                # Process JSON of selected availability times, which is in the form
                # {'start': 'HH:mm', 'end': 'HH:mm'}
                times_list = []
                for time in availability_times:
                    times_list.append(json.loads(time))

                # Need to convert from date object to datetime object
                date_start = datetime.combine(availability_form.cleaned_data.get('start_date'), datetime.max.time())
                date_end = datetime.combine(availability_form.cleaned_data.get('end_date'), datetime.max.time())

                # Assign starting date to another variable that will be incremented until the end date
                date_current = date_start

                # Number of created availabilities
                num_of_created_availabilities = 0

                # Get staff id
                staff_id = Staff.objects.filter(user=request.user).first().id

                # Create availabilities starting at the start date until the end date
                while date_current <= date_end:
                    # Only add availabilities at the selected days of the week
                    if date_current.strftime("%A").lower() in availability_days:

                        # Process each element in the times list, which contains: {'start': 'HH:mm', 'end': 'HH:mm'}
                        for time in times_list:
                            # Creating datetime objects for the start and end times
                            start_datetime_object = datetime.strptime(
                                date_current.strftime('%Y/%m/%d ') + time.get('start'), '%Y/%m/%d %H:%M')
                            end_datetime_object = datetime.strptime(
                                date_current.strftime('%Y/%m/%d ') + time.get('end'), '%Y/%m/%d %H:%M')

                            # Fetch all existing appointments at current date of the while loop
                            existing_appointments_at_current_date = list(Appointment.objects.filter(
                                start_date__year=date_current.year,
                                start_date__month=date_current.month,
                                start_date__day=date_current.day,
                                staff_id=staff_id
                            ).values('start_date', 'end_date'))

                            # Check if availability collides with already existing appointment objects.
                            # Availability collides if either the start or end time is in between the start and end
                            # time of an existing Appointment object OR if the Availability has the exact same start and
                            # end time of an existing Appointment object
                            for existing_appt in existing_appointments_at_current_date:
                                if existing_appt.get('start_date') < start_datetime_object < existing_appt.get(
                                        'end_date') \
                                        or existing_appt.get('start_date') < end_datetime_object < existing_appt.get(
                                        'end_date') \
                                        or (existing_appt.get('start_date') == start_datetime_object
                                            and existing_appt.get(
                                            'end_date') == end_datetime_object):
                                    # Don't create Appointment objects since they collide with existing Appointments
                                    # and display error message
                                    messages.error(request,
                                                   'The availability was not created. There already exists an '
                                                   'appointment or availability between ' +
                                                   start_datetime_object.strftime(
                                                       '%Y-%m-%d %H:%M') + ' and ' + end_datetime_object.strftime(
                                                       '%Y-%m-%d %H:%M') + '.')
                                    return redirect('appointments:add_availabilities')

                            staff_id = Staff.objects.filter(user=request.user).first().id

                            # Create new Appointment object
                            apt = Appointment.objects.create(staff_id=staff_id, patient=None,
                                                             start_date=start_datetime_object,
                                                             end_date=end_datetime_object)
                            apt.save()

                            num_of_created_availabilities += 1

                    # Increment to next day
                    date_current += timedelta(days=1)

                # If the selected days of the week do not match any of the dates between start and end date
                if num_of_created_availabilities == 0:
                    messages.error(request,
                                   'No dates exist for the selected days of the week.')
                    return redirect('appointments:add_availabilities')

                # Reset the form
                availability_form = AvailabilityForm()

                # Display success message
                messages.success(request, 'The availabilities have been created.')

                if request.POST.get('Create and Return'):
                    return redirect('appointments:index')

        else:
            availability_form = AvailabilityForm()

        return render(request, 'appointments/add_availabilities.html', {
            'availability_form': availability_form
        })


@login_required
@never_cache
def book_appointments(request):
    """
    this function handles the booking of one or multiple appointments at the same time in one template page
    ("book_appointments.html") and makes sure that the proper success messages are displayed
    :param request: the type of request that is processed in the "book_appointments.html" template page
    :return: returns the specific template that is either rendered or redirected to based on the user input logic
    (either redirected to the "index.html" template page or rendered back to the default "book_appointments.html" template page)
    """

    staff_id = get_assigned_staff_id_by_patient_id(request.user.id)
    staff_name = get_users_names(Staff.objects.get(id=staff_id).user_id)

    if request.method == 'POST' and request.POST.get('Book Appointment'):
        appointment_id = request.POST.get('Book Appointment')

        # books a single appointment by adding the patient's id to the appointment's patient_id column
        book_appointment(appointment_id, request.user)

        # success message to show to the user if the existing appointment was booked successfully
        messages.success(request, 'The appointment was booked successfully.')
        return redirect('appointments:book_appointments')

    if request.method == 'POST' and request.POST.get('Book Selected Appointments'):
        appointment_ids = request.POST.getlist('booking_ids[]')

        # books all selected appointments by adding the patient's id to the appointment's patient_id column
        for appointment_id in appointment_ids:
            book_appointment(appointment_id, request.user)

        # success message to show user if appointments were booked
        messages.success(request, 'The selected appointments were booked successfully.')
        return redirect('appointments:index')

    return render(request, 'appointments/book_appointments.html', {
        'appointments': Appointment.objects.filter(patient=None, staff=staff_id).all(),
        'staff_name': staff_name
    })


@login_required
@never_cache
def cancel_appointments_or_delete_availabilities(request):
    """
    this function handles the cancellation and/or deletion of one or multiple appointments and/or availabilities at the same time in one template page
    ("cancel_appointments.html") and makes sure that the proper success messages are displayed
    :param request: the type of request that is processed in the "cancel_appointments.html" template page
    :return: returns the specific template that is either rendered or redirected to based on the user input logic
    (either redirected to the "index.html" template page or rendered back to the default "cancel_appointments.html" template page)
    """

    is_staff = get_is_staff(request.user.id)

    if request.user.is_staff:
        staff_name = ''
        logged_in_filter = Q(staff_id=request.user.staff.id)

    else:
        staff_id = get_assigned_staff_id_by_patient_id(request.user.id)
        staff_name = get_users_names(Staff.objects.get(id=staff_id).user_id)
        logged_in_filter = Q(patient_id=request.user.id)

    if request.method == 'POST' and request.POST.get('Cancel Appointment'):
        booked_id = request.POST.get('Cancel Appointment')

        # cancels a single appointment by setting the patient's id in the appointment's patient_id column to "None"
        cancel_appointments(booked_id)

        # success message to show to the user if the existing appointment was cancelled successfully
        messages.success(request, 'The appointment was canceled successfully.')
        return redirect('appointments:cancel_appointments_or_delete_availabilities')

    if request.method == 'POST' and request.POST.get('Delete Availability'):
        unbooked_id = request.POST.get('Delete Availability')

        # deletes a single existing doctor availability by deleting the entire appointment object row from the database
        delete_availabilities(unbooked_id)

        # success message to show to the doctor/staff if the existing availability was deleted successfully
        messages.success(request, 'The availability was deleted successfully.')
        return redirect('appointments:cancel_appointments_or_delete_availabilities')

    if request.method == 'POST' and request.POST.get('Cancel Selected Appointments'):
        booked_ids = request.POST.getlist('booked_ids[]')

        # cancels all selected existing appointments by setting the patient's id in the appointment's patient_id column to "None"
        for booked_id in booked_ids:
            cancel_appointments(booked_id)

        # success message to show to the doctor/staff if all selected existing appointments were cancelled successfully
        messages.success(request, 'The appointments were canceled successfully.')
        return redirect('appointments:index')

    if request.method == 'POST' and request.POST.get('Delete Selected Availabilities'):
        unbooked_ids = request.POST.getlist('booked_ids[]')

        # deletes all selected existing doctor availabilities by deleting the entire respective appointment object rows from the database
        for unbooked_id in unbooked_ids:
            delete_availabilities(unbooked_id)

        # success message to show to the doctor/staff if all selected existing availabilities were deleted successfully
        messages.success(request, 'The availabilities were deleted successfully.')
        return redirect('appointments:index')

    return render(request, 'appointments/cancel_appointments.html', {
        'appointments': Appointment.objects.filter(logged_in_filter).all(),
        'is_staff': is_staff,
        'staff_name': staff_name
    })

