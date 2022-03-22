import os.path

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from Covigo.settings import HOST_NAME
from accounts.models import Flag, Staff, Patient
from pathlib import Path
import smtplib
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
import shortuuid
from qrcode.main import make
from qrcode.image.pil import PilImage


def get_flag(staff_user, patient_user):
    """
    Returns the flag assigned to a patient_user by a staff_user
    @param staff_user: Staff user object
    @param patient_user: Patient user object
    @return: The patient's flag assigned by the staff if it exists, or None if it doesn't
    """
    try:
        flag = staff_user.staffs_created_flags.get(patient=patient_user)
        return flag
    except Flag.DoesNotExist:
        return None


def get_user_from_uidb64(uidb64):
    try:
        # urlsafe_base64_decode() decodes to bytestring
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    return user


def get_superuser_staff_model():
    """
    Returns the staff object of the superuser or creates one if it doesn't exist
    @return: the superuser's staff object
    """
    try:
        superuser = User.objects.filter(is_superuser=True).get()
        try:
            return superuser.staff
        except Staff.DoesNotExist:
            Staff.objects.create(user=superuser)
            return superuser.staff
    # TODO: specify which exception instead of the generic one
    except Exception:
        return None


def generate_and_send_email(user, subject, template):
    """
    Generate and send a "reset password" email for a user
    @param user: The user whose password is to be reset
    @param subject: The name to give the email's subject
    @param template: The template to use for the email to send
    @return: void
    """
    c = {
        'email': user.email,
        'host_name': HOST_NAME,
        'site_name': 'Covigo',
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'user': user,
        'token': default_token_generator.make_token(user),
    }
    email = render_to_string(template, c)
    send_email_to_user(user, subject, email)


# takes a user, subject, and message as params and sends the user an email
def send_email_to_user(user, subject, message):
    """
    Send an email to a user
    @param user: The user to send the email to
    @param subject: The subject of the email to send
    @param message: The message of the email to send
    @return: void
    """
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    email = 'shahdextra@gmail.com'
    pwd = 'roses12345!%'
    s.login(email, pwd)
    s.sendmail(email, user.email, f"Subject: {subject}\n{message}")
    s.quit()
    return None


# takes a user, user's phone number, and message as params and sends a text message
def send_sms_to_user(user, user_phone, message):
    account = "AC77b343442a4ec3ea3d0258ea5c597289"
    token = "f9a14a572c2ab1de3683c0d65f7c962b"
    client = Client(account, token)

    try:
        message = client.messages.create(to=user_phone, from_="+16626727846",
                                         body=message)
    except TwilioRestException as e:
        print(e)

    return None


def get_or_generate_patient_code(patient, prefix="A"):
    """
    Get a patient's profile code or generate one if it doesn't exist
    @param patient: The patient whose code is to be fetched
    @param prefix: The prefix to give to the code. A is the default prefix
    @return: The patient's profile code
    """
    # Shortuuid docs recommends removing characters (like 0 and O) that can be confused.
    # It sounds reasonable so I decided to do that.
    shortuuid.set_alphabet("23456789ABCDEFGHJKLMNPQRSTUVWXYZ")
    if not patient.code:
        code = shortuuid.uuid()[:9]

        # Regenerate the code if it exists
        while Patient.objects.filter(code=code).exists():
            code = shortuuid.uuid()[:9]

        code = prefix + code

        patient.code = code
        patient.save()
        return patient.code
    else:
        return patient.code


def get_or_generate_patient_profile_qr(user_id):
    """
    Get the path to a patient's qr code image, or generate the image if it doesn't exist.
    @param user_id: The patient whose qr code is to be fetched
    @return: Path to the qr code image file
    """
    user = User.objects.get(id=user_id)

    # Only generate qr codes for patient users
    if not user.is_staff:
        # Get or generate the unique patient code
        patient = Patient.objects.get(user=user)
        patient_code = get_or_generate_patient_code(patient)

        # Link to store in the qr code
        data = f"{HOST_NAME}/accounts/profile/{str(patient_code)}"

        # Create path to store generated qr code image
        path = f"accounts/qrs/{str(patient_code)}.png"
        Path("accounts/static/accounts/qrs").mkdir(parents=True, exist_ok=True)

        if os.path.exists(path):
            return path
        else:
            # Generate the qr code
            img: PilImage = make(data)
            img.save("accounts/static/" + path)
            return path
    else:
        return None


# Deprecated function, but I'll leave it here in case it becomes useful later.
def reset_username_to_email_or_phone(user):
    # Try setting username to the email if it exists
    email = user.email
    if email:
        user.username = email
        user.save()
        return

    # If the user doesn't have an email, set it to the phone number
    phone_number = user.profile.phone_number
    if phone_number:
        user.username = phone_number
        user.save()
        return

    # If the user has neither an email nor a phone number, raise an exception
    # TODO: Raise a more specific exception here
    raise Exception


# Deprecated function, but I'll leave it here in case it becomes useful later.
def set_username_to_blank(user):
    try:
        user.username = " "
        user.save()

    except IntegrityError:
        user_to_reset = User.objects.get(username=" ")
        reset_username_to_email_or_phone(user_to_reset)
        user.username = " "
        user.save()


def get_current_recovered_case_count():
    """
    A recovered case is someone who HAD covid but later RECOVERED via NEGATIVE TEST
    @return:
    """
    confirmed = Q(is_confirmed=True)
    negative = Q(is_negative=True)
    return Patient.objects.filter(confirmed & negative).count()


def get_current_positive_case_count():
    """
    A positive case is someone who HAS COVID and DID NOT TEST NEGATIVE YET
    @return:
    """
    confirmed = Q(is_confirmed=True)
    not_negative = Q(is_negative=False)
    return Patient.objects.filter(confirmed & not_negative).count()


def get_unconfirmed_and_negative_case_count():
    """
    This is for cases where someone NEVER HAD COVID and TESTED NEGATIVE, thus being "in the clear".
    @return: The number of unconfirmed cases who tested negative
    """
    not_confirmed = Q(is_confirmed=False)
    negative = Q(is_negative=True)
    return Patient.objects.filter(not_confirmed & negative).count()


def get_unconfirmed_and_untested_count():
    """
    This is for cases where someone NEVER HAD COVID and DID NOT TEST YET, thus need ing to take a Covid test.
    After their test, they will either become a confirmed case or an unconfirmed, negative case.
    @return: The number of unconfirmed cases whoa re still untested
    """
    not_confirmed = Q(is_confirmed=False)
    not_negative = Q(is_negative=False)
    return Patient.objects.filter(not_confirmed & not_negative).count()


def get_current_negative_case_count():
    """
    This is for all cases where someone's latest test is negative.
    They may be an unconfirmed case who tested negative or a confirmed case who recovered from having Covid
    @return: The number of cases whose most recent test was negative
    """
    return Patient.objects.filter(is_negative=True).count()


def get_current_confirmed_case_count():
    """
    This is for all cases where someone is a confirmed case.
    A confirmed case is anyone who has covid right now, or had Covid earlier and recovered.
    @return: The total number of confirmed Covid cases
    """
    return Patient.objects.filter(is_confirmed=True).count()


def get_assigned_staff_id_by_patient_id(patient_id):
    """
    Returns the staff id of the assigned user for the patient.
    @param patient_id: patient user id
    @return: assigned staff id or else 0
    """
    try:
        return Patient.objects.values_list('assigned_staff_id', flat=True).get(user_id=patient_id)
    except Exception:
        return 0


def get_users_names(user_id):
    """
    Returns the users first name and last name
    @param user_id: the user's user id
    @return: a string containing the users first and last name else empty string
    """
    try:
        user = User.objects.get(id=user_id)
        return f"{user.first_name} {user.last_name}"
    except User.DoesNotExist:
        return ""


def get_is_staff(user_id):
    """
    Returns the is_staff column for a user id in the user table
    @param user_id: the user's user id
    @return: is_staff column else -1 if the user does not exist
    """
    try:
        return User.objects.get(id=user_id).is_staff
    except User.DoesNotExist:
        return -1
