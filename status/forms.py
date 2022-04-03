import datetime
from django import forms
from django.forms import Form, TextInput, ModelForm, FileInput, DateInput

from accounts.forms import CHARFIELD_CLASS


class TestResultForm(Form):
    date_today = datetime.datetime.now()
    date_three_months = date_today - datetime.timedelta(days=90)

    test_type = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "PCR, antigen, etc.",
                "class": CHARFIELD_CLASS
            }
        )
    )

    test_date = forms.DateField(
        initial=date_today.strftime("%Y-%m-%d"),
        required=True,
        widget=forms.widgets.DateInput(
            attrs={
                'class': 'border border-black px-1 rounded-md',
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
                'class': 'p-2'
            }
        ),
        choices=[('0', 'Negative'), ('1', 'Positive')]
    )

    test_file = forms.FileField()