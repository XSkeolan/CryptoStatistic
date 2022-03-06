from django.forms import Form
from django import forms


class UserForm(Form):
    user_id = forms.CharField(label='User Id', widget=forms.TextInput(attrs={
        "class": 'form-control',
        'placeholder': 'User Id'
    }))
    api_key = forms.CharField(label='API Key', widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'API Key'
    }))
    time_refresh = forms.IntegerField(label='Time to refresh(sec)', min_value=1, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Time to refresh(sec)'
    }))


class InfoForm(Form):
    date_start = forms.DateField(required=True, label="start", widget=forms.DateInput(attrs={
        'class': 'form-control',
        'placeholder': 'Дата начала(в формате YYYY-MM-DD)',
        'autocomplete': 'off',
        'pattern': '(?:19|20)[0-9]{2}-(?:(?:0[1-9]|1[0-2])-(?:0[1-9]|1[0-9]|2[0-9])|(?:(?!02)(?:0[1-9]|1[0-2])-(?:30))|(?:(?:0[13578]|1[02])-31))'
    }))
    date_end = forms.DateField(required=True, label="end", widget=forms.DateInput(attrs={
        'class': 'form-control',
        'placeholder': 'Дата окончания(в формате YYYY-MM-DD)',
        'autocomplete': 'off',
        'pattern': '(?:19|20)[0-9]{2}-(?:(?:0[1-9]|1[0-2])-(?:0[1-9]|1[0-9]|2[0-9])|(?:(?!02)(?:0[1-9]|1[0-2])-(?:30))|(?:(?:0[13578]|1[02])-31))'
    }))
