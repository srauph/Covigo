import datetime
from django import forms
from django.forms import Form, TextInput, ModelForm, FileInput, DateInput

from accounts.forms import CHARFIELD_CLASS
from accounts.models import Patient




class TestResultForm(ModelForm):
    class Meta:
        model = Patient
        fields = ["test_type",
                  "test_date"
                  "test_result",
                  "test_file"
                  ]

        date_today = datetime.datetime.now()
        date_three_months = date_today - datetime.timedelta(days=90)

        widgets = {
            "test_type": TextInput(
                attrs={
                    "placeholder": "PCR, antigen, etc.",
                    "class": CHARFIELD_CLASS
                }
            ),
            "test_date": DateInput(
                attrs={
                    'class': 'border border-black px-1 rounded-md',
                    'type': 'date',
                    'min': date_three_months.strftime("%Y-%m-%d"),
                    'max': date_today.strftime("%Y-%m-%d")
                }
            ),
            "test_result": TextInput(
                attrs={
                    "placeholder": "PCR, antigen, etc.",
                    "class": CHARFIELD_CLASS
                }
            ),
            "test_file": FileInput(
               ),
        }
