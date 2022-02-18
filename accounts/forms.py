from django.forms import ModelForm, TextInput, CheckboxSelectMultiple
from django.contrib.auth.models import User
from accounts.models import Profile


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'groups'
        ]
        widgets = {
            'username': TextInput(attrs={
                'class': 'border-2 rounded-md border-slate-800'
            }),
            'email': TextInput(attrs={
                'class': 'border-2 rounded-md border-slate-800'
            }),
            'groups': CheckboxSelectMultiple()
        }


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = [
            'phone_number'
        ]
        widgets = {
            'phone_number': TextInput(attrs={
                'class': 'border-2 rounded-md border-slate-800'
            }),
        }
