from django import forms
from symptoms.models import Symptom


class CreateSymptomForm(forms.ModelForm):
    class Meta:
        model = Symptom
        fields = ['name', 'description']
    name = forms.CharField(
        label='Symptom Name',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. fever, cough, cold, etc.',
            'required': True,
            'size': 50,
            'class': 'w-full rounded border px-4 py-2'
        })
    )
    description = forms.CharField(
        label='Symptom Description',
        widget=forms.Textarea(attrs={
            'placeholder': 'e.g. individual may lose sense of smell and/or taste, etc.',
            'max_length': 100,
            'required': True,
            'rows': 3,
            'cols': 50,
            'class': 'w-full px-4 py-2 rounded border align-middle'
        })
    )
