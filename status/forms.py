import datetime
from django import forms
from django.forms import Form, TextInput, ModelForm, FileInput, DateInput

from accounts.forms import CHARFIELD_CLASS
from accounts.models import Patient

"""
This task has three major parts. 

1)This first part is going to be "patient reporting their test result". It will be a page where patients submit a form with four fields:

--The first field will be a DATETIME OR TEXT field where the PATIENT inputs the TEST RESULT'S DATE

--The second field will be a TEXT field where the PATIENT inputs the TYPE of test (eg pcr, rapid antigen, etc. should be 
a test so as new testing methods come out we don't have an outdated system)

--The third field will be a TEXT field where the PATIENT inputs the RESULT of the test (positive, negative, inconclusive, whatever)

--The fourth field will be a FILE INPUT where the patient can upload PROOF of the test result (as pdf or whatever)


2)The second part is the staff "validating" the patient's test report. He will get access to the file input to see it and 
verify the patient's input. He can then set the "is_negative" boolean field. Idk if the staff should be allowed to override 
the patient's text input or not, maybe for now make it readonly and we'll put it permissions based.

3)The third part is the system handling the result and auto assigning a doctor if the result is not negative.
"""


class TestResultForm(ModelForm):
    class Meta:
        model = Patient
        fields = ["test_results"]

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
