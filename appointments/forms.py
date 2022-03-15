import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.forms.formsets import BaseFormSet


DAYS = (('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'))

SLOT_HOURS = [tuple([x, x]) for x in range(0, 24)]
SLOT_MINUTES = [tuple([x, x]) for x in range(0, 65, 5)]


# class TimeForm(forms.Form):
#     start_time_hour = forms.IntegerField(widget=forms.Select(choices=TIME_HOUR))
#     start_time_minute = forms.IntegerField(widget=forms.Select(choices=TIME_MINUTE))
#
#     end_time_hour = forms.IntegerField(widget=forms.Select(choices=TIME_HOUR))
#     end_time_minute = forms.IntegerField(widget=forms.Select(choices=TIME_MINUTE))
#
#
# # This class is for custom form validation
# class BaseTimeFormSet(BaseFormSet):
#
#     def clean(self):
#
#         if any(self.errors):
#             return
#
#         # Validate start and end times with the slot duration time
#         slot_duration_in_minutes = int(self.data.get('slot_duration_hours')) * 60 + int(
#             self.data.get('slot_duration_minutes'))
#         # Validation error is handled by the AvailabilityForm. This check is just to prevent modulo division by 0
#         if slot_duration_in_minutes == 0:
#             raise ValidationError("")
#
#         for index, element in enumerate(self.forms):
#             if element.cleaned_data:
#                 start_time_hour = element.cleaned_data['start_time_hour']
#                 start_time_minute = element.cleaned_data['start_time_minute']
#                 end_time_hour = element.cleaned_data['end_time_hour']
#                 end_time_minute = element.cleaned_data['end_time_minute']
#
#                 # Ensure that start and end times are valid
#                 if start_time_hour > end_time_hour or (
#                         start_time_hour == end_time_hour and start_time_minute == end_time_minute):
#                     raise ValidationError(
#                         "Start and end times are not valid"
#                     )
#
#                 # Validate start and end time duration can be divisible by the slot duration
#                 start_in_minutes = start_time_hour * 60 + start_time_minute
#                 end_in_minutes = end_time_hour * 60 + end_time_minute
#                 if (end_in_minutes - start_in_minutes) % slot_duration_in_minutes != 0:
#                     raise ValidationError(
#                         "Start and end times do not fall within the selected timeslot duration"
#                     )
#
#                 # Check if start and end times do not overlap
#                 if index + 1 < len(self.forms):
#                     next_element = self.forms[index + 1]
#                     next_start_time_hour = next_element.cleaned_data['start_time_hour']
#                     next_start_time_minute = next_element.cleaned_data['start_time_minute']
#                     next_end_time_hour = next_element.cleaned_data['end_time_hour']
#                     next_end_time_minute = next_element.cleaned_data['end_time_minute']
#
#                     next_start_in_minutes = next_start_time_hour * 60 + next_start_time_minute
#                     next_end_in_minutes = next_end_time_hour * 60 + next_end_time_minute
#
#                     if start_in_minutes == next_start_in_minutes and end_in_minutes == next_end_in_minutes:
#                         raise ValidationError(
#                             "Duplicate start and end times"
#                         )
#
# if start_in_minutes < next_start_in_minutes < end_in_minutes or start_in_minutes < next_end_in_minutes <
# end_in_minutes: raise ValidationError( "Start and end times are overlapping" )


class AvailabilityForm(forms.Form):
    availability_days = forms.MultipleChoiceField(choices=DAYS,
                                                  widget=forms.CheckboxSelectMultiple(),
                                                  required=True)

    slot_duration_hours = forms.IntegerField(widget=forms.Select(choices=SLOT_HOURS), initial='1', required=True)
    slot_duration_minutes = forms.IntegerField(widget=forms.Select(choices=SLOT_MINUTES), required=True)

    date_today = datetime.datetime.now()
    date_one_year = date_today + datetime.timedelta(days=365)

    start_date = forms.DateField(initial=date_today, required=True, widget=forms.widgets.DateInput(
        attrs={'type': 'date', 'min': date_today, 'max': date_one_year}))

    end_date = forms.DateField(required=True, widget=forms.widgets.DateInput(
        attrs={'type': 'date', 'min': date_today, 'max': date_one_year}))


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
