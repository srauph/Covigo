from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm, TextInput, CheckboxSelectMultiple, Select, CharField
from django.contrib.auth.models import User
from accounts.models import Profile

STAFF_PATIENT_CHOICES = (
    (True, 'Staff User'),
    (False, 'Patient User')
)

GUEST_CHARFIELD_CLASS = \
    'appearance-none ' \
    'rounded-none ' \
    'relative ' \
    'block ' \
    'w-full ' \
    'px-3 ' \
    'py-2 ' \
    'border ' \
    'border-gray-300 ' \
    'placeholder-gray-500 ' \
    'text-gray-900 ' \
    'focus:outline-none ' \
    'focus:ring-indigo-500 ' \
    'focus:border-indigo-500 ' \
    'focus:z-10 ' \
    'sm:text-sm'

GUEST_CHARFIELD_CLASS_TOP = GUEST_CHARFIELD_CLASS + ' rounded-t-md'
GUEST_CHARFIELD_CLASS_MIDDLE = GUEST_CHARFIELD_CLASS
GUEST_CHARFIELD_CLASS_BOTTOM = GUEST_CHARFIELD_CLASS + ' rounded-b-md'
GUEST_CHARFIELD_CLASS_STANDALONE = GUEST_CHARFIELD_CLASS + ' rounded-md'

CHARFIELD_CLASS = "w-full h-8 px-2 bg-slate-100 rounded-md border border-slate-400"
SELECTION_CLASS = "w-full h-8 px-1 bg-slate-100 rounded-md border border-slate-400"
CHECKBOX_CLASS = "p-2"


class CreateUserForm(ModelForm):
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
                    "class": CHARFIELD_CLASS
                }
            ),
            "groups": CheckboxSelectMultiple(
                attrs={
                    "class": CHECKBOX_CLASS
                }
            ),
            "is_staff": Select(
                choices=STAFF_PATIENT_CHOICES,
                attrs={
                    "class": SELECTION_CLASS
                }
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


class CreateProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = [
            "phone_number"
        ]
        widgets = {
            "phone_number": TextInput(
                attrs={
                    "class": CHARFIELD_CLASS
                }
            )
        }

    def clean_phone_number(self):
        # TODO: Sanitize to a "valid" phone number like 5141112222
        cleaned_phone_number = self.cleaned_data.get("phone_number")
        if cleaned_phone_number != "" and Profile.objects.filter(phone_number=cleaned_phone_number).exists():
            raise ValidationError(
                "Phone number already in use by another user."
            )
        return cleaned_phone_number


class RegisterUserForm(ModelForm):
    username = CharField(
        # Set required to false here to override django's builtin popup.
        # The "required-ness" will be checked in clean_username()
        required=False,
        widget=TextInput(
            attrs={
                "placeholder": "Username",
                "class": GUEST_CHARFIELD_CLASS_STANDALONE
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id')
        super(RegisterUserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name"
        ]
        widgets = {
            "email": TextInput(
                attrs={
                    "placeholder": "Email Address",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            ),

            "first_name": TextInput(
                attrs={
                    "placeholder": "First Name",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            ),
            "last_name": TextInput(
                attrs={
                    "placeholder": "Last Name",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            ),
        }

    def clean_username(self):
        cleaned_username = self.cleaned_data.get("username")
        if cleaned_username == "":
            raise ValidationError(
                "Please provide a username."
            )
        if cleaned_username != "" and User.objects.filter(email=cleaned_username).exclude(id=self.user_id).exists():
            raise ValidationError(
                "Username already in use by another user."
            )
        return cleaned_username

    def clean_email(self):
        cleaned_email = self.cleaned_data.get("email")
        if cleaned_email == "":
            raise ValidationError(
                "Please provide an email."
            )

        if cleaned_email != "" and User.objects.filter(email=cleaned_email).exclude(id=self.user_id).exists():
            raise ValidationError(
                "Email already in use by another user."
            )
        return cleaned_email

    def clean_first_name(self):
        cleaned_first_name = self.cleaned_data.get("first_name")
        if cleaned_first_name == "":
            raise ValidationError(
                "Please provide your first name."
            )
        return cleaned_first_name

    def clean_last_name(self):
        cleaned_last_name = self.cleaned_data.get("last_name")
        if cleaned_last_name == "":
            raise ValidationError(
                "Please provide your last name."
            )
        return cleaned_last_name


class RegisterProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id')
        super(RegisterProfileForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Profile
        fields = [
            "phone_number",
            "address",
            "postal_code",
        ]
        widgets = {
            "phone_number": TextInput(
                attrs={
                    "placeholder": "Phone Number",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            ),
            "address": TextInput(
                attrs={
                    "placeholder": "Address",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            ),
            "postal_code": TextInput(
                attrs={
                    "placeholder": "Postal Code",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            )
        }

    def clean_phone_number(self):
        # TODO: Sanitize to a "valid" phone number like 5141112222
        cleaned_phone_number = self.cleaned_data.get("phone_number")
        if cleaned_phone_number == "":
            raise ValidationError(
                "Please provide a phone number."
            )
        if cleaned_phone_number != "" and Profile.objects.filter(phone_number=cleaned_phone_number).exclude(user=User.objects.get(id=self.user_id)).exists():
            raise ValidationError(
                "Phone number already in use by another user."
            )
        return cleaned_phone_number

    def clean_address(self):
        cleaned_address = self.cleaned_data.get("address")
        if cleaned_address == "":
            raise ValidationError(
                "Please provide your address."
            )
        return cleaned_address

    def clean_postal_code(self):
        cleaned_postal_code = self.cleaned_data.get("postal_code")
        if cleaned_postal_code == "":
            raise ValidationError(
                "Please provide your postal code."
            )
        return cleaned_postal_code


class EditUserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id')
        super(EditUserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "groups"
        ]
        widgets = {
            "username": TextInput(
                attrs={
                    "class": CHARFIELD_CLASS
                }
            ),
            "email": TextInput(
                attrs={
                    "class": CHARFIELD_CLASS
                }
            ),

            "first_name": TextInput(
                attrs={
                    "class": CHARFIELD_CLASS
                }
            ),
            "last_name": TextInput(
                attrs={
                    "class": CHARFIELD_CLASS
                }
            ),
            "groups": CheckboxSelectMultiple(
                attrs={
                    "class": CHECKBOX_CLASS
                }
            ),
        }

    def clean_email(self):
        cleaned_email = self.cleaned_data.get("email")
        if cleaned_email != "" and User.objects.filter(email=cleaned_email).exclude(id=self.user_id).exists():
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


class EditProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id')
        super(EditProfileForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Profile
        fields = [
            "phone_number",
            "address",
            "postal_code",
        ]
        widgets = {
            "phone_number": TextInput(
                attrs={
                    "class": CHARFIELD_CLASS
                }
            ),
            "address": TextInput(
                attrs={
                    "class": CHARFIELD_CLASS
                }
            ),
            "postal_code": TextInput(
                attrs={
                    "class": CHARFIELD_CLASS
                }
            )
        }

    def clean_phone_number(self):
        # TODO: Sanitize to a "valid" phone number like 5141112222
        cleaned_phone_number = self.cleaned_data.get("phone_number")
        if cleaned_phone_number != "" and Profile.objects.filter(phone_number=cleaned_phone_number).exclude(user=User.objects.get(id=self.user_id)).exists():
            raise ValidationError(
                "Phone number already in use by another user."
            )
        return cleaned_phone_number


class SetPasswordForm(SetPasswordForm):
    error_messages = {
        'password_mismatch': 'The two password fields didn’t match.'
    }
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                'autocomplete': 'new-password',
                'placeholder': 'New Password',
                'class': GUEST_CHARFIELD_CLASS_TOP
            }
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'autocomplete': 'new-password',
                'placeholder': 'Confirm Password',
                'class': GUEST_CHARFIELD_CLASS_BOTTOM
            }
        ),
    )