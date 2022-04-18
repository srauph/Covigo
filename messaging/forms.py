from django import forms

from Covigo.form_field_classes import *
from messaging.models import MessageContent, MessageGroup


class CreateMessageContentForm(forms.ModelForm):
    class Meta:
        model = MessageContent
        fields = ['content']

    content = forms.CharField(
        label='Content',
        widget=forms.Textarea(
            attrs={
                'placeholder': "e.g. I'm having difficulty breathing, my body temperature is rising, etc.",
                'max_length': 100,
                'required': True,
                'rows': 3,
                'cols': 50,
                'class': TEXTAREA_CLASS
            }
        )
    )


class CreateMessageGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.recipient = kwargs.pop('recipient')
        super(CreateMessageGroupForm, self).__init__(*args, **kwargs)

    class Meta:
        model = MessageGroup
        fields = ['title', 'priority']

    title = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': "e.g. Concern with loss of smell",
                'required': True,
                'size': 50,
                'class': TEXTINPUT_CLASS
            }
        )
    )
    priority = forms.ChoiceField(
        widget=forms.RadioSelect(
            attrs={
                'required': True,
                'class': 'p-2'
            }
        ),
        choices=[('0', 'Low'), ('1', 'Medium'), ('2', 'High')]
    )


class ReplyForm(forms.ModelForm):
    class Meta:
        model = MessageContent
        fields = ['content']

    content = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3,
                'cols': 50,
                'placeholder': "Reply..."
            }
        )
    )
