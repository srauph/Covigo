import os.path
import shortuuid
import smtplib
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from Covigo.settings import HOST_NAME
from accounts.models import Flag, Staff, Patient
from pathlib import Path
from qrcode import make
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


def reset_password_email_generator(user, subject, template):
    """
    Generate and send a "reset password" email for a user
    @param user: The user whose password is to be reset
    @param subject: The name to give the email's subject
    @param template: The template to use for the email to send
    @return: void
    """
    c = {
        "email": user.email,
        'domain': '127.0.0.1:8000',
        'site_name': 'Website',
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "user": user,
        'token': default_token_generator.make_token(user),
        'protocol': 'http',
    }
    email = render_to_string(template, c)
    send_email_to_user(user, subject, email)


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


def get_or_generate_patient_code(patient):
    """
    Get a patient's profile code or generate one if it doesn't exist
    @param patient: The patient whose code is to be fetched
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


def get_active_flag_count_from_patient(user_id):
    """
    Gets and returns the active flag count for a patient by staff.
    @param user_id: patient user ID
    @return: returns active flag count or else 0
    """
    try:
        return Flag.objects.filter(patient_id=user_id, is_active=1).count()
    except Exception:
        return 0


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
        return User.objects.get(id=user_id).first_name + " " + User.objects.get(id=user_id).last_name
    except Exception:
        return ""


def get_is_staff(user_id):
    """
    Returns the is_staff column for a user id in the user table
    @param user_id: the user's user id
    @return: is_staff column else -1 if the user does not exist
    """
    try:
        return User.objects.get(id=user_id).is_staff
    except Exception:
        return -1
