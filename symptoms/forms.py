from django import forms

from Covigo.form_field_classes import *
from symptoms.models import Symptom


class CreateSymptomForm(forms.ModelForm):
    class Meta:
        model = Symptom
        fields = ['name', 'description']

    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. fever, cough, cold, etc.',
            'size': 50,
            'class': TEXTINPUT_CLASS
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'e.g. individual may lose sense of smell and/or taste, etc.',
            'rows': 3,
            'cols': 50,
            'class': TEXTAREA_CLASS
        })
    )
