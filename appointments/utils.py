from appointments.models import Appointment


def cancel_appointments(appointment_id):
    """
    sets the patient's id in the appointment's patient_id column to "None" in order to "cancel" the appointment
    :param appointment_id: the specific appointment's appointment id
    :return: void
    """
    booked = Appointment.objects.get(id=appointment_id)
    booked.patient = None
    booked.save()


def delete_availabilities(appointment_id):
    """
    deletes the entire appointment object row from the database in order to "delete" the availability
    :param appointment_id: the specific appointment's appointment id
    :return: void
    """
    unbooked = Appointment.objects.get(id=appointment_id)
    unbooked.delete()
