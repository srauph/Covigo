from django.contrib import admin

from accounts.models import Patient
#from .models import Code
from .models import Profile
# Register your models here.


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    pass
admin.site.register(Profile)