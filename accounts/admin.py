from django.contrib import admin

from accounts.models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    pass