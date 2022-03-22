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


class Patient(models.Model):
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
    is_recovered = models.BooleanField(default=False)
    is_quarantining = models.BooleanField(default=False)
    code = models.CharField(max_length=255)

    def get_assigned_staff_user(self):
        return self.assigned_staff.user

    def __str__(self):
        return f"{self.user}_patient"


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

