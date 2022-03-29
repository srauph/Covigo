from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random

class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    phone_number = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    postal_code = models.CharField(max_length=255, blank=True)
    preferences = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.user}_profile"


class Staff(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    def get_assigned_patient_users(self):
        return User.objects.filter(patient__in=self.assigned_patients.all())

    def __str__(self):
        return f"{self.user}_staff"

    def get_active_flag_count(self):
        """
        Gets and returns the active number of flags issued by this staff.
        @return: returns active flag count or else 0
        """
        try:
            return Flag.objects.filter(staff=self.user, is_active=True).count()
        except:
            return 0

class Patient(models.Model):
    """
    is_confirmed: A confirmed patient is one who had covid, either now or previously.
    is_negative: A negative patient is one who is proven to not have covid via a negative test.
                 A patient who isn't negative either has covid or is a "probable case"
    is_quarantining: A quarantining patient is one who is in isolation.
                     This applies whether they have covid or not (eg living with someone with covid)
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    assigned_staff = models.ForeignKey(
        Staff,
        related_name="assigned_patients",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    is_confirmed = models.BooleanField(default=False)
    is_negative = models.BooleanField(default=False)
    is_quarantining = models.BooleanField(default=False)
    code = models.CharField(max_length=255)

    def get_assigned_staff_user(self):
        try:
            return self.assigned_staff.user
        except AttributeError:
            return None

    def __str__(self):
        return f"{self.user}_patient"

    def get_active_flag_count(self, staff_user):
        """
        Gets and returns the active flag count for a patient by staff.
        @return: returns active flag count or else 0
        """
        try:
            return Flag.objects.filter(patient=self.user, staff=staff_user, is_active=True).count()
        except Exception:
            return 0


class Flag(models.Model):
    staff = models.ForeignKey(
        User,
        related_name="staffs_created_flags",
        on_delete=models.CASCADE
    )
    patient = models.ForeignKey(
        User,
        related_name="patients_assigned_flags",
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['staff', 'patient'], name='unique_flag')
        ]

    def __str__(self):
        return f"{self.patient}_flaggedby_{self.staff}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

