from django.forms import ModelForm
from django.contrib.auth.models import User
from accounts.models import Profile


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = [
            'email',
            'groups'
        ]