import datetime
from django import forms
from django.core.exceptions import ValidationError

DAYS = (('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'))

SLOT_HOURS = [tuple([x, x]) for x in range(0, 24)]
SLOT_MINUTES = [tuple([x, x]) for x in range(0, 65, 5)]


class AvailabilityForm(forms.Form):
    availability_days = forms.MultipleChoiceField(choices=DAYS,
                                                  widget=forms.CheckboxSelectMultiple(attrs={'class': 'days_checkbox'}),
                                                  required=True)

    slot_duration_hours = forms.IntegerField(widget=forms.Select(choices=SLOT_HOURS,attrs={'class':'border border-black px-1 rounded-md'}), initial='1', required=True)
    slot_duration_minutes = forms.IntegerField(widget=forms.Select(choices=SLOT_MINUTES,attrs={'class':'border border-black px-1 rounded-md'}), required=True)

    date_today = datetime.datetime.now()
    date_one_year = date_today + datetime.timedelta(days=365)

    start_date = forms.DateField(initial=date_today.strftime("%Y-%m-%d"), required=True, widget=forms.widgets.DateInput(
        attrs={'class': 'border border-black px-1 rounded-md', 'type': 'date', 'min': date_today.strftime("%Y-%m-%d"),
               'max': date_one_year.strftime("%Y-%m-%d")}))

    end_date = forms.DateField(required=True, widget=forms.widgets.DateInput(
        attrs={'class': 'border border-black px-1 rounded-md', 'type': 'date', 'min': date_today.strftime("%Y-%m-%d"),
               'max': date_one_year.strftime("%Y-%m-%d")}))

    # Validate start and end times with the slot duration time
    def clean_slot_duration_hours(self):
        slot_duration_in_minutes = int(self.data.get('slot_duration_hours')) * 60 + int(
            self.data.get('slot_duration_minutes'))
        if slot_duration_in_minutes == 0:
            raise ValidationError(
                "Invalid slot duration"
            )
        return self.data.get('slot_duration_hours')

    def clean_start_date(self):
        start_date = self.data.get('start_date')
        end_date = self.data.get('end_date')
        if start_date > end_date:
            raise ValidationError(
                "Invalid start and end dates"
            )
        return datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
