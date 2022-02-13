from django.db import models
from django.contrib.auth.models import User


class Appointment(models.Model):
    patient = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name='appointments_patient',
        on_delete=models.CASCADE
    )
    staff = models.ForeignKey(
        User,
        related_name='appointments_staff',
        on_delete=models.CASCADE
    )
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"appointment_{self.staff}_{self.patient}_{self.start_date}"
