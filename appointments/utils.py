from appointments.models import Appointment


def cancel_appointments(appointment_id):
    """
    cancels the booked appointment with the corresponding appointment id:
    this is done by setting the patient_id column of the specific booked appointment to "None"
    @params: appointment_id: the appointment's id
    @return: void
    """
    booked = Appointment.objects.get(id=appointment_id)
    booked.patient = None
    booked.save()



def delete_availabilities(appointment_id):
    """
    deletes the entire appointment object row from the database in order to "delete" the availability
    :param appointment_id: the specific appointment's appointment id
    :return: None
    """
    unbooked = Appointment.objects.get(id=appointment_id)
    unbooked.delete()

    
def book_appointment(appointment_id, user):
    """
    books an appointment in the corresponding appointment availability by setting the patient column to the user
    @params: appointment_id: the  appointment's id
    @params: user: the current patient user object
    @return: void
    """
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.patient = user
    appointment.save()


def rebook_appointment_with_new_doctor(new_doctor_id, old_doctor_id, patient):
    """
    this function is called when a patient has a doctor reassignment:
    rebooks the appointments a patient had with an old, previously assigned, doctor to the new doctor if they have an availability at
    the same time as the appointment time with their original doctor (if there is no corresponding availability, the appointment is cancelled)
    @params: new_doctor_id: the newly assigned doctor's id
    @params: old_doctor_id: the old, previously assigned, doctor's id
    @params: patient: the specific patient user object
    @return: void
    """
    # if the newly assigned doctor is the same, do nothing
    try:
        if int(new_doctor_id) == int(old_doctor_id):
            return
    except TypeError:
        return

    patient_id = patient.id
    booked_appointments = []
    try:
        booked_appointments = Appointment.objects.filter(staff_id=old_doctor_id, patient_id=patient_id).all()

    # if the patient has no booked appointments with the old, previously assigned, doctor, do nothing
    except Appointment.DoesNotExist:
        return

    new_doctor_availabilities = Appointment.objects.filter(patient=None, staff_id=new_doctor_id).all()

    # if the newly assigned doctor does not have any availabilities, cancel all the patient's current appointments
    if len(new_doctor_availabilities) == 0:
        for appointment in booked_appointments:
            appointment.patient_id = None
            appointment.save()

    # if the newly assigned doctor has availabilities
    else:
        # check each booked appointment for a corresponding availability at the same day and time with the newly assigned doctor
        for appointment in booked_appointments:
            found_corresponding_availability = False
            for availability in new_doctor_availabilities:
                # if a corresponding availability is found, cancel the corresponding booked appointment with the old, previously assigned, doctor and book a new
                #  appointment at the same day and time with the newly assigned doctor
                if is_appointment_and_availability_same_datetime(appointment, availability):
                    appointment.patient_id = None
                    availability.patient = patient
                    appointment.save()
                    availability.save()
                    found_corresponding_availability = True

                    break
            # if a corresponding availability is not found, just cancel the booked appointment with the old, previously assigned, doctor
            if not found_corresponding_availability:
                appointment.patient_id = None
                appointment.save()


def is_appointment_and_availability_same_datetime(appointment, availability):
    """
    returns a boolean if the appointment and availability start and end dates are the same, up to the minute
    @params : appointment: an appointment object of a booked appointment with the old, previously assigned, doctor
    @params : availability: an appointment object of an availability with the newly assigned doctor
    @return : True if both arguments have the same start and end dates, else False
    """
    appointment.start_date = appointment.start_date.replace(microsecond=0, second=0)
    appointment.end_date = appointment.end_date.replace(microsecond=0, second=0)
    availability.start_date = availability.start_date.replace(microsecond=0, second=0)
    availability.end_date = availability.end_date.replace(microsecond=0, second=0)

    return appointment.start_date == availability.start_date and appointment.end_date == availability.end_date

