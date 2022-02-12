from django.db import models
from django.contrib.auth.models import User


class Symptom:
    name = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField()
    date_created = models.DateTimeField()
    date_updated = models.DateTimeField()


class PatientSymptom:
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE(),
    )
    symptom = models.OneToOneField(
        Symptom,
        on_delete=models.CASCADE()
    )
    data = models.TextField()
    is_hidden = models.BooleanField()
    is_viewed = models.BooleanField()
    due_date = models.DateTimeField()
    date_created = models.DateTimeField()
    date_updated = models.DateTimeField()
