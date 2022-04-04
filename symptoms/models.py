from django.db import models
from django.contrib.auth.models import User


class Symptom(models.Model):
    users = models.ManyToManyField(
        User,
        related_name="symptoms",
        through='PatientSymptom',
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PatientSymptom(models.Model):
    user = models.ForeignKey(
        User,
        related_name="patient_symptoms",
        on_delete=models.CASCADE,
    )
    symptom = models.ForeignKey(
        Symptom,
        related_name="patient_symptoms",
        on_delete=models.CASCADE,
    )
    data = models.TextField(blank=True, null=True)
    # Approved 0, Rejected -1, Useless for Patient View (Patient Resubmit) -2
    status = models.IntegerField(default=0, null=True)
    is_hidden = models.BooleanField(default=False)
    is_viewed = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    due_date = models.DateTimeField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}_{self.symptom}"
