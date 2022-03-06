import datetime
from cProfile import label
from random import choices

from django.core.exceptions import ValidationError
from django import forms
from django.core.exceptions import ValidationError
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
TIME_TYPE = [('days', 'days'),
             ('weeks', 'weeks'),
             ('months', 'months')]


class TimeForm(forms.Form):
    start_time_hour = forms.IntegerField(widget=forms.Select(choices=TIME_HOUR))
    start_time_minute = forms.IntegerField(widget=forms.Select(choices=TIME_MINUTE))

    end_time_hour = forms.IntegerField(widget=forms.Select(choices=TIME_HOUR))
    end_time_minute = forms.IntegerField(widget=forms.Select(choices=TIME_MINUTE))


# This class is for custom form validation
class BaseTimeFormSet(BaseFormSet):
    def clean(self):

        if any(self.errors):
            return

        # Validate start and end times with the slot duration time
        slot_duration_in_minutes = int(self.data.get('slot_duration_hours')) * 60 + int(
                                    self.data.get('slot_duration_minutes'))
        for form in self.forms:
            if form.cleaned_data:
                start_time_hour = form.cleaned_data['start_time_hour']
                start_time_minute = form.cleaned_data['start_time_minute']
                end_time_hour = form.cleaned_data['end_time_hour']
                end_time_minute = form.cleaned_data['end_time_minute']

                # Ensure that start and end times are valid
                if start_time_hour > end_time_hour:
                    raise ValidationError(
                        "Start and end times are not valid"
                    )

                # Validate start and end time duration can be divisible by the slot duration
                start_in_minutes = start_time_hour*60 + start_time_minute
                end_time_minutes = end_time_hour*60 + end_time_minute
                if (end_time_minutes-start_in_minutes) % slot_duration_in_minutes != 0:
                    raise ValidationError(
                        "Start and end times do not fall within the selected timeslot duration"
                    )


class AvailabilityForm(forms.Form):
    availability_days = forms.MultipleChoiceField(choices=DAYS,
                                                  widget=forms.CheckboxSelectMultiple(),
                                                  required=True)

    slot_duration_hours = forms.IntegerField(widget=forms.Select(choices=SLOT_HOURS), required=True)
    slot_duration_minutes = forms.IntegerField(widget=forms.Select(choices=SLOT_MINUTES), required=True)

    date_today = datetime.datetime.now()
    date_one_year = date_today + datetime.timedelta(days=365)

    date_until = forms.DateField(initial=date_today.strftime("%Y-%m-%d"), required=True, widget=forms.widgets.DateInput(
        attrs={'type': 'date', 'min': date_today.strftime("%Y-%m-%d"), 'max': date_one_year.strftime("%Y-%m-%d")}))
