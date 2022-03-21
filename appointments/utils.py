from appointments.models import Appointment


def cancel_appointments(appointment_id):
    booked = Appointment.objects.get(id=appointment_id)
    booked.patient = None
    booked.save()
