from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from Covigo.exceptions import UserNotPatientNorStaffException


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


class Flag(models.Model):
    staff = models.ForeignKey(
        User,
        related_name="flagged_patients",
        on_delete=models.CASCADE
    )
    patient = models.ForeignKey(
        User,
        related_name="staffs_flagged_by",
        on_delete=models.CASCADE
    )
    date_created = models.DateTimeField

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['staff', 'patient'], name='unique_flag')
        ]

    def __str__(self):
        return f"{self.patient}_{self.staff}"


# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     try:
#         instance.profile.save()
#     # TODO change Exception with the proper exception name later
#     except Exception:
#         print("User has no profile")
#     if hasattr(instance, 'patient'):
#         instance.patient.save()
#     elif hasattr(instance, 'staff'):
#         instance.staff.save()
#     else:
#         raise UserNotPatientNorStaffException
