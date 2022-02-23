from django import forms
from django.forms import ModelForm

from messaging.models import MessageContent, MessageGroup


class CreateMessageContentForm(forms.ModelForm):
    class Meta:
        model = MessageContent
        fields = ['content']

    content = forms.CharField(
        label='Content',
        widget=forms.Textarea(
            attrs={
                'placeholder': "e.g. those drugs you gave me are hitting hard fam..",
                'max_length': 100,
                'required': True,
                'rows': 3,
                'cols': 50,
                'class': 'w-full bg-slate-100 text-base px-2 py-1 rounded border border-slate-400 align-middle'
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
                'placeholder': "e.g. I'm dying, help im pregnant, etc.",
                'required': True,
                'size': 50,
                'class': 'w-full h-8 px-2 bg-slate-100 rounded-md border border-slate-400'
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
                'class': "w-full bg-slate-100 text-base px-4 py-2 rounded border border-slate-400 align-middle",
                'rows': 3,
                'cols': 50,
                'placeholder': "Reply..."
            }
        )
    )
