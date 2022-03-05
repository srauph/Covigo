from cProfile import label
from random import choices

from django import forms
from django.forms.formsets import BaseFormSet

from appointments.models import Appointment

TIME_SLOTS = [
    ('', ''),
    (15, '15 minutes'),
    (30, '30 minutes'),
    (45, '45 minutes'),
    (60, '1 hour'),
    (120, '2 hours'),
    (180, '3 hours'),
    (240, '4 hours'),
    (300, '5 hours'),
    (360, '6 hours'),
    (420, '7 hours'),
    (480, '8 hours'),
    (540, '9 hours'),
    (600, '10 hours'),
    (660, '11 hours'),
    (720, '12 hours'),
    (780, '13 hours'),
    (840, '14 hours'),
    (900, '15 hours'),
    (960, '16 hours'),
    (1020, '17 hours'),
    (1080, '18 hours'),
    (1140, '19 hours'),
    (1200, '20 hours'),
    (1260, '21 hours'),
    (1320, '22 hours'),
    (1380, '23 hours'),
]

ADVANCE = [
    ('', ''),
    (1, '1 month'),
    (2, '2 months'),
    (3, '3 months'),
    (4, '4 months'),
    (5, '5 months'),
    (6, '6 months'),
    (7, '7 months'),
    (8, '8 months'),
    (9, '9 months'),
    (10, '10 months'),
    (11, '11 months'),
    (12, '12 months'),
]

DAYS = (('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'))

SLOT_HOURS = [tuple([x, x]) for x in range(0, 24)]
SLOT_MINUTES = [tuple([x, x]) for x in range(0, 65, 5)]

TIME_HOUR = [tuple([x, x]) for x in range(1, 13)]
TIME_MINUTE = [tuple([x, str(x).zfill(2)]) for x in range(0, 60, 5)]
TIME_AM_PM = [('AM', 'AM'), ('PM', 'PM')]

class TimeForm(forms.Form):
    start_time_hour = forms.IntegerField(widget=forms.Select(choices=TIME_HOUR))
    start_time_minute = forms.IntegerField(widget=forms.Select(choices=TIME_MINUTE))
    start_time_am_pm = forms.CharField(widget=forms.Select(choices=TIME_AM_PM))

    end_time_hour = forms.IntegerField(widget=forms.Select(choices=TIME_HOUR))
    end_time_minute = forms.IntegerField(widget=forms.Select(choices=TIME_MINUTE))
    end_time_am_pm = forms.CharField(widget=forms.Select(choices=TIME_AM_PM))

class BaseTimeFormSet(BaseFormSet):
    def clean(self):
        print(1)



class AvailabilityForm(forms.Form):
    availability_days = forms.MultipleChoiceField(choices=DAYS,
                                                  widget=forms.CheckboxSelectMultiple())

    slot_duration_hours = forms.IntegerField(widget=forms.Select(choices=SLOT_HOURS))
    slot_duration_minutes = forms.IntegerField(widget=forms.Select(choices=SLOT_MINUTES))




