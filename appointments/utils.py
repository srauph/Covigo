from appointments.models import Appointment


def cancel_appointments(appointment_id):
    """
    Cancels the booking appointment with the corresponding appointment id.
    This is done by setting the patient_id of the appointment to None
    @params: appointment_id: the appointment ID
    @return: None
    """
    booked = Appointment.objects.get(id=appointment_id)
    booked.patient = None
    booked.save()


def book_appointment(appointment_id, user):
    """
    Books an appointment in the corresponding appointment availability by setting the patient column to the user
    @params: appointment_id: the  appointment's id
    @params: user: the current patient user object
    @return: None
    """
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.patient = user
    appointment.save()


def rebook_appointment_with_new_doctor(new_doctor_id, old_doctor_id, patient):
    """
    This function is called when a patient has a doctor reassignment.
    Rebooks a patient's appointments they had with the old doctor to the new doctor if they have an availability at
    the same time as the appointment time with their original doctor.
    If there is no corresponding availability, the appointment is cancelled.
    @params: appointment_id: the appointment ID
    @return: None
    """
    # if the doctor is the same do nothing
    if int(new_doctor_id) == int(old_doctor_id):
        return

    patient_id = patient.id
    booked_appointments = []
    try:
        booked_appointments = Appointment.objects.filter(staff_id=old_doctor_id, patient_id=patient_id).all()

    # if the patient has no booked appointments with the old doctor do nothing
    except Appointment.DoesNotExist:
        return

    new_doctor_availabilities = Appointment.objects.filter(patient=None, staff_id=new_doctor_id).all()

    # if the new doctor does not have any availabilities, cancel all patients appointments
    if len(new_doctor_availabilities) == 0:
        for appointment in booked_appointments:
            appointment.patient_id = None
            appointment.save()

    # if the doctor has availabilities
    else:
        # check each booked appointment for a corresponding availability at the same day and time with the new doctor
        for appointment in booked_appointments:
            found_corresponding_availability = False
            for availability in new_doctor_availabilities:
                # if a corresponding availability is found cancel the booking with the old doctor and book an
                #  appointment at the same day and time with the new doctor
                if is_appointment_and_availability_same_datetime(appointment, availability):
                    appointment.patient_id = None
                    availability.patient = patient
                    appointment.save()
                    availability.save()
                    found_corresponding_availability = True

                    break
            # if a corresponding availability is not found just cancel the booking with the old doctor
            if not found_corresponding_availability:
                appointment.patient_id = None
                appointment.save()


def is_appointment_and_availability_same_datetime(appointment, availability):
    """
    Returns a bool if the appointment and availability start and end dates are the same, up to the minute.
    @params : appointment: an appointment object of a booked appointment with the old doctor
    @params : availability: an appointment object of an availability with the new doctor
    @return : True if both arguments have the same start and end dates
    """
    appointment.start_date = appointment.start_date.replace(microsecond=0, second=0)
    appointment.end_date = appointment.end_date.replace(microsecond=0, second=0)
    availability.start_date = availability.start_date.replace(microsecond=0, second=0)
    availability.end_date = availability.end_date.replace(microsecond=0, second=0)

    return appointment.start_date == availability.start_date and appointment.end_date == availability.end_date
