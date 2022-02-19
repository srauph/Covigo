from django.core.exceptions import ValidationError
from django.forms import ModelForm, TextInput, CheckboxSelectMultiple, BooleanField, Select
from django.contrib.auth.models import User
from accounts.models import Profile

STAFF_PATIENT_CHOICES = (
    (True, 'Staff User'),
    (False, 'Patient User')
)


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = [
            "email",
            "groups",
            "is_staff"
        ]
        widgets = {
            "email": TextInput(
                attrs={
                    "class": "border rounded-md border-slate-600"
                }
            ),
            "groups": CheckboxSelectMultiple(),
            "is_staff": Select(
                choices=STAFF_PATIENT_CHOICES
            ),
        }

    def clean_email(self):
        cleaned_email = self.cleaned_data.get("email")
        if cleaned_email != "" and User.objects.filter(email=cleaned_email).exists():
            raise ValidationError(
                "Email already in use by another user."
            )
        return cleaned_email

    def clean_groups(self):
        cleaned_groups = self.cleaned_data.get("groups")
        # TODO: Discuss the possibility of having no group and fix error and if: != 1 if we enforce having at least one
        if len(cleaned_groups) > 1:
            raise ValidationError(
                "Cannot select more than one group."
            )
        return cleaned_groups


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = [
            "phone_number"
        ]
        widgets = {
            "phone_number": TextInput(
                attrs={
                    "class": "border rounded-md border-slate-600"
                }
            )
        }

    def clean_phone_number(self):
        cleaned_phone_number = self.cleaned_data.get("phone_number")
        if cleaned_phone_number != "" and Profile.objects.filter(phone_number=cleaned_phone_number).exists():
            raise ValidationError(
                "Phone number already in use by another user."
            )
        return cleaned_phone_number
