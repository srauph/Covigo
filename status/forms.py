import datetime
from django import forms
from django.forms import Form

from accounts.forms import *


class TestResultForm(Form):
    date_today = datetime.datetime.now()
    date_three_months = date_today - datetime.timedelta(days=90)

    test_type = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "PCR, antigen, etc.",
                "class": TEXTINPUT_CLASS
            }
        )
    )

    test_date = forms.DateField(
        initial=date_today.strftime("%Y-%m-%d"),
        required=True,
        widget=forms.widgets.DateInput(
            attrs={
                'class': DATEINPUT_CLASS,
                'type': 'date',
                'min': date_three_months.strftime("%Y-%m-%d"),
                'max': date_today.strftime("%Y-%m-%d")
            }
        )
    )

    test_result = forms.ChoiceField(
        widget=forms.RadioSelect(
            attrs={
                'required': True,
                'class': CHECKBOX_CLASS
            }
        ),
        choices=[('0', 'Negative'), ('1', 'Positive'), ('2', 'Inconclusive')]
    )

    test_file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                'required': True,
                'class': FILEINPUT_CLASS_HIDDEN
            }
        )
    )