import datetime
from cProfile import label
from random import choices

from django import forms
from django.forms.formsets import BaseFormSet

from appointments.models import Appointment

DAYS = (('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'))

SLOT_HOURS = [tuple([x, x]) for x in range(0, 24)]
SLOT_MINUTES = [tuple([x, x]) for x in range(0, 65, 5)]

TIME_HOUR = [tuple([x, x]) for x in range(1, 24)]
TIME_MINUTE = [tuple([x, str(x).zfill(2)]) for x in range(0, 60, 5)]

class TimeForm(forms.Form):
    start_time_hour = forms.IntegerField(widget=forms.Select(choices=TIME_HOUR))
    start_time_minute = forms.IntegerField(widget=forms.Select(choices=TIME_MINUTE))

    end_time_hour = forms.IntegerField(widget=forms.Select(choices=TIME_HOUR))
    end_time_minute = forms.IntegerField(widget=forms.Select(choices=TIME_MINUTE))

class BaseTimeFormSet(BaseFormSet):
    def clean(self):
        print(1)

class DatePickerInput(forms.DateInput):
    input_type = 'date'

class AvailabilityForm(forms.Form):
    availability_days = forms.MultipleChoiceField(choices=DAYS,
                                                  widget=forms.CheckboxSelectMultiple())

    slot_duration_hours = forms.IntegerField(widget=forms.Select(choices=SLOT_HOURS))
    slot_duration_minutes = forms.IntegerField(widget=forms.Select(choices=SLOT_MINUTES))

    date_today = datetime.datetime.now()
    date_one_year = date_today + datetime.timedelta(days=365)

    date_until = forms.DateField(initial=date_today.strftime("%Y-%m-%d"), widget=forms.widgets.DateInput(attrs={'type': 'date', 'min':date_today.strftime("%Y-%m-%d"), 'max':date_one_year.strftime("%Y-%m-%d")}))





