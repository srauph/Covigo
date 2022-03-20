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


def rebook_appointment_with_new_doctor(doctor_id, appointment_id, user):
    """
    This function is called when a patient has a doctor reassignment.
    Rebooks a patient's appointments they had with the old doctor to the new doctor if they have an availability at
    the same time as the appointment time with their original doctor.
    If there is no corresponding availability, the appointment is cancelled.
    @params: appointment_id: the appointment ID
    @return: None
    """



