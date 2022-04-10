import os.path
import random
import shortuuid
import smtplib

from django.contrib.auth.models import User
from django.contrib.staticfiles.management.commands import collectstatic
from django.db import IntegrityError, connection
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from Covigo.settings import HOST_NAME
from accounts.models import Flag, Staff, Patient
from accounts.preferences import SystemMessagesPreference

from geopy import distance
from pathlib import Path
from qrcode.image.pil import PilImage
from qrcode.main import make
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


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


#takes a user, subject, and body as params and sends the user an email
def send_email_to_user(user, subject, body):
    """
    Sends an email to a user
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
        body = client.messages.create(
            to=user.profile.phone_number,
            from_="+16626727846",
            body=body
        )
    except TwilioRestException as e:
        print(e)

    return None


def send_system_message_to_user(user, message=None, template=None, subject=None, c=None):
    if user.profile.preferences and SystemMessagesPreference.NAME.value in user.profile.preferences:
        preferences = user.profile.preferences[SystemMessagesPreference.NAME.value]
    else:
        preferences = None

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
            command = collectstatic.Command()
            command.collect()
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
    @return: The number of confirmed cases who tested negative and recovered
    """

    confirmed = Q(is_confirmed=True)
    negative = Q(is_negative=True)
    return Patient.objects.filter(confirmed & negative).count()


def get_current_positive_case_count():
    """
    A positive case is someone who HAS COVID and DID NOT TEST NEGATIVE YET
    @return: The number of confirmed cases who tested positive
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
    @return: The number of unconfirmed cases who are still untested
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


# generate 5 digit otp
def generate_otp_code():
    number_list = [x for x in range(10)]
    code_items = []

    for i in range(5):
        num = random.choice(number_list)
        code_items.append(num)

    code_string = "".join(str(item) for item in code_items)
    return code_string


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_distance_of_all_doctors_to_postal_code(postal_code):
    doc_dict = []
    all_doctors = User.objects.raw(
        "SELECT * FROM `auth_user` INNER JOIN `auth_user_groups` ON (`auth_user`.`id` = `auth_user_groups`.`user_id`) INNER JOIN `auth_group` ON (`auth_user_groups`.`group_id` = `auth_group`.`id`) LEFT OUTER JOIN `accounts_profile` ON (`auth_user`.`id` = `accounts_profile`.`user_id`) JOIN `postal_codes` ON (`accounts_profile`.`postal_code` = `postal_codes`.POSTAL_CODE) WHERE `auth_group`.`name` = %s",
        ['doctor'])
    c = connection.cursor()
    c.execute('SELECT * FROM postal_codes WHERE POSTAL_CODE = %s', [postal_code])
    r = dictfetchall(c)
    patient_postal_code_lat_long = (float(r[0]['LATITUDE']), float(r[0]['LONGITUDE']))

    for docs in all_doctors:
        doctor_postal_code_lat_long = (float(docs.LATITUDE), float(docs.LONGITUDE))
        distance_patient_to_doctor = distance.distance(patient_postal_code_lat_long, doctor_postal_code_lat_long).m
        doctor_number_of_patients = docs.staff.assigned_patients.count()
        doc_dict.append((docs, int(distance_patient_to_doctor), doctor_number_of_patients))
    sorted_doc_dict = sorted(doc_dict, key=lambda tup: tup[1])
    return sorted_doc_dict


def return_closest_with_least_patients_doctor(postal_code):
    docs_list = get_distance_of_all_doctors_to_postal_code(postal_code)
    sliced_list = docs_list[0:4]
    sorted_sliced_doc_list = sorted(sliced_list, key=lambda tup: tup[2])
    closest_with_least_patients = sorted_sliced_doc_list[0]
    return closest_with_least_patients[0]


def convert_dict_of_bools_to_list(dict_to_process):
    output_list = []

    for i in dict_to_process:
        if dict_to_process[i]:
            output_list.append(i)

    return output_list


def hour_options_generator(number_of_hours, step=1):
    hours_list = []

    for i in range(step, number_of_hours+step, step):
        if i == 1:
            hours_list.append((i, "1 hour"))
        else:
            hours_list.append((i, f"{i} hours"))

    return tuple(hours_list)
