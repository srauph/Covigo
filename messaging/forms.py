from django import forms
from messaging.models import MessageContent, MessageGroup


class CreateMessageForm(forms.Form):
    class Meta:
        model = MessageContent, MessageGroup

    recipient = forms.CharField(
            label='Recipient',
            widget=forms.TextInput(attrs={
                'placeholder': "e.g. doctor strange, wanda, etc.",
                'required': True,
                'size': 50,
                'class': 'w-full rounded border px-4 py-2'
            })
        )
    title = forms.CharField(
            label='Subject',
            widget=forms.TextInput(attrs={
                'placeholder': "e.g. I'm dying, help im pregnant, etc.",
                'required': True,
                'size': 50,
                'class': 'w-full rounded border px-4 py-2'
            })
        )
    priority = forms.ChoiceField(
            label='Priority',
            widget=forms.RadioSelect(attrs={
                'required': True
            }),
            choices=[('0', 'Low'), ('1', 'Medium'), ('2', 'High')]
        )
    content = forms.CharField(
            label='Content',
            widget=forms.Textarea(attrs={
                'placeholder': "e.g. those drugs you gave me are hitting hard fam..",
                'max_length': 100,
                'required': True,
                'rows': 3,
                'cols': 50,
                'class': 'w-full px-4 py-2 rounded border align-middle'
            })
        )


class ReplyForm(forms.ModelForm):
    class Meta:
        model = MessageContent
        fields = ['content']

    content = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={'class': "w-full bg-slate-100 text-base px-4 py-2 rounded border border-slate-400 align-middle",
                   'rows': 3,
                   'cols': 50,
                   'placeholder': "Reply..."})
    )
