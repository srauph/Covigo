from django.db import models
from django.contrib.auth.models import User


class Staff(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    phone_number = models.CharField(max_length=255)
    address = models.TextField()
    postal_code = models.CharField(max_length=255)


class Patient(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
    )
    phone_number = models.CharField(max_length=255)
    address = models.TextField()
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    is_confirmed = models.BooleanField(default=False)
    is_recovered = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    is_quarantining = models.BooleanField(default=False)
    code = models.CharField(max_length=255)