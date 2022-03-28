import smtplib

from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from Covigo.settings import HOST_NAME
from accounts.preferences import SystemMessagesPreference
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


#takes a user, subject, and body as params and sends the user an email
def send_email_to_user(user, subject, body):
    """
    Send an email to a user
    @param user: The user to send the email to
    @param subject: The subject of the email to send
    @param body: The body of the email to send
    @return: void
    """
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    email = 'shahdextra@gmail.com'
    pwd = 'roses12345!%'
    s.login(email, pwd)
    s.sendmail(email, user.email, f"Subject: {subject}\n{body}")
    s.quit()
    return None


# takes a user, user's phone number, and body as params and sends a text body
def send_sms_to_user(user, body):
    account = "AC77b343442a4ec3ea3d0258ea5c597289"
    token = "f9a14a572c2ab1de3683c0d65f7c962b"
    client = Client(account, token)

    try:
        body = client.messages.create(to=user.profile.phone_number, from_="+16626727846",
                                      body=body)
    except TwilioRestException as e:
        print(e)

    return None


def _send_system_message_from_template(user, template, c=None, is_email=True):
    """
    Generate and send a system message a user
    @param user: The user who the system message should be sent to
    @param template: The template to use for the system message to send
    @param c: Context variables to use to generate the system message
    @param is_email: Whether the system message is an email or not
    @return: void
    """

    if not c:
        c = dict()

    c['email'] = user.email
    c['host_name'] = HOST_NAME
    c['site_name'] = 'Covigo'
    c['user'] = user
    c['uid'] = urlsafe_base64_encode(force_bytes(user.pk))

    if is_email:
        body = template["body"]
        subject = template["subject"]
        email = render_to_string(body, c)
        send_email_to_user(user, subject, email)
    else:
        body = template
        message = render_to_string(body, c)
        send_sms_to_user(user, message)


def send_system_message_to_user(user, message=None, template=None, subject=None, c=None):
    preferences = user.profile.preferences[SystemMessagesPreference.NAME.value]

    if user.email and (not preferences or preferences[SystemMessagesPreference.EMAIL.value]):
        if template:
            _send_system_message_from_template(user, template.get("email"), c, is_email=True)
        else:
            send_email_to_user(user, message, subject)

    if user.profile.phone_number and (not preferences or preferences[SystemMessagesPreference.SMS.value]):
        if template:
            _send_system_message_from_template(user, template.get("sms"), c, is_email=False)
        else:
            send_sms_to_user(user, message)
