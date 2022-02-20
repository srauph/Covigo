from django import forms
from messaging.models import MessageContent


class ReplyForm(forms.ModelForm):
    class Meta:
        model = MessageContent
        fields = ['content']

    content = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={'class': "w-full text-base px-4 py-2 rounded border align-middle",
                   'rows': 3,
                   'cols': 50,
                   'placeholder': "Reply..."})
    )
