from django import forms
from django.contrib.auth.models import User

from accounts.models import Patient
from symptoms.models import Symptom, PatientSymptom


class CreateSymptomForm(forms.ModelForm):
    class Meta:
        model = Symptom
        fields = ['name', 'description']

    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. fever, cough, cold, etc.',
            'required': True,
            'size': 50,
            'class': 'w-full h-8 px-2 bg-slate-100 rounded-md border border-slate-400'
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'e.g. individual may lose sense of smell and/or taste, etc.',
            'max_length': 100,
            'required': True,
            'rows': 3,
            'cols': 50,
            'class': 'w-full bg-slate-100 text-base px-2 py-1 rounded border border-slate-400 align-middle'
        })
    )
