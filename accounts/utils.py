from accounts.models import Flag, Staff
from django.contrib.auth.models import User
import smtplib
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

# Returns the flag assigned to a patient_user by a staff_user
def get_flag(staff_user, patient_user):
    try:
        flag = staff_user.staffs_created_flags.get(patient=patient_user)
        return flag
    except Flag.DoesNotExist:
        return None


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

#takes a user, subject, and message as params and sends the user an email
def sendMailToUser(user, subject, message):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    email = 'shahdextra@gmail.com'
    pwd = 'roses12345!%'
    s.login(email,pwd)
    s.sendmail(email, user.username, f"Subject: {subject}\n{message}")
    s.quit()
    return None


#takes a user, user's phone number, and message as params and sends a text message
def sendSMSToUser(user, user_phone, message):
    account = "AC77b343442a4ec3ea3d0258ea5c597289"
    token = "f9a14a572c2ab1de3683c0d65f7c962b"
    client = Client(account, token)

    try:
        message = client.messages.create(to=user_phone, from_="+16626727846",
                                         body=message)
    except TwilioRestException as e:
        print(e)

    return None