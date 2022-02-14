from django.forms import Form
from django import forms


class UserForm(Form):
    user_id = forms.CharField(label='User Id', widget=forms.TextInput(attrs={
        "class": '',
        'placeholder': 'User Id'
    }))
    api_key = forms.CharField(label='API Key', widget=forms.TextInput(attrs={
        'class': '',
        'placeholder': 'API Key'
    }))
    time_refresh = forms.IntegerField(label='Time to refresh(sec)', min_value=1, widget=forms.NumberInput(attrs={
        'class': '',
        'placeholder': 'Time to refresh(sec)'
    }))
