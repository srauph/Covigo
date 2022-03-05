from cProfile import label

from django import forms
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


class AvailabilityForm(forms.Form):
    availability_slot_time = forms.CharField(label='Time slot', widget=forms.Select(choices=TIME_SLOTS))
    availability_advance = forms.CharField(label='Advance', widget=forms.Select(choices=ADVANCE))
