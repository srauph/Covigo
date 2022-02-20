from accounts.models import Flag, Staff
from django.contrib.auth.models import User


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
        except User.staff.RelatedObjectDoesNotExist:
            Staff.objects.create(user=superuser)
            return superuser.staff
    # TODO: specify which exception instead of the generic one
    except Exception:
        return None