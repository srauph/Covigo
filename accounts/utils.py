from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from Covigo.settings import HOST_NAME, PRODUCTION_MODE
from accounts.models import Flag, Staff, Patient

from pathlib import Path
from qrcode import *

import smtplib
import shortuuid
import os.path


# Returns the flag assigned to a patient_user by a staff_user
def get_flag(staff_user, patient_user):
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
    if PRODUCTION_MODE:
        c = {
            'email': user.email,
            'domain': 'covigo.ddns.net',
            'site_name': 'Covigo',
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': default_token_generator.make_token(user),
            'protocol': 'https',
        }
    else:
        c = {
            'email': user.email,
            'domain': '127.0.0.1:8000',
            'site_name': 'Covigo',
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            'token': default_token_generator.make_token(user),
            'protocol': 'http',
        }
    email = render_to_string(template, c)
    send_email_to_user(user, subject, email)


def send_email_to_user(user, subject, message):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    email = 'shahdextra@gmail.com'
    pwd = 'roses12345!%'
    s.login(email,pwd)
    s.sendmail(email, user.email, f"Subject: {subject}\n{message}")
    s.quit()


def get_or_generate_code(patient):
    # Shortuuid docs recommends removing characters (like 0 and O) that can be confused.
    # It sounds reasonable so I decided to do that.
    shortuuid.set_alphabet("23456789ABCDEFGHJKLMNPQRSTUVWXYZ")
    if not patient.code:
        code = shortuuid.uuid()[:9]

        # Regenerate the code if it exists
        while Patient.objects.filter(code=code).exists():
            code = shortuuid.uuid()[:9]

        patient.code = code
        patient.save()
        return patient.code
    else:
        return patient.code


def generate_profile_qr(user_id):
    user = User.objects.get(id = user_id)

    # Only generate qr codes for patient users
    if not user.is_staff:
        # Get or generate the unique patient code
        patient = Patient.objects.get(user=user)
        patient_code = get_or_generate_code(patient)

        # Link to store in the qr code
        data = f"{HOST_NAME}/accounts/profile/{str(patient_code)}"

        # Create path to store generated qr code image
        path = f"accounts/qrs/{str(patient_code)}.png"
        Path("accounts/static/accounts/qrs").mkdir(parents=True, exist_ok=True)

        if os.path.exists(path):
            return path
        else:
            # Generate the qr code
            img = make(data)
            img.save("accounts/static/"+path)
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
