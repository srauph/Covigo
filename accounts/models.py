from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from Covigo.exceptions import UserNotPatientNorStaffException, UserHasNoProfileException


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    phone_number = models.CharField(max_length=255)
    address = models.TextField()
    postal_code = models.CharField(max_length=255)


class Staff(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )


class Patient(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
    )
    is_confirmed = models.BooleanField(default=False)
    is_recovered = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    is_quarantining = models.BooleanField(default=False)
    code = models.CharField(max_length=255)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    # TODO change Exception with the proper exception name later
    except Exception:
        print("User has no profile")
    if hasattr(instance, 'patient'):
        instance.patient.save()
    elif hasattr(instance, 'staff'):
        instance.staff.save()
    else:
        raise UserNotPatientNorStaffException
