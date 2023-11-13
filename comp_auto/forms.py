from django import forms
from django.contrib.auth.models import User

class RegistrationForm(forms.Form):
    
    registrationUsername = forms.CharField(label='Username', widget=forms.TextInput(attrs={'id': 'registrationUsername'}))
    registrationEmail = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'id': 'registrationEmail'}))
    # registrationPhoneNo = forms.CharField(label='Phone Number', widget=forms.NumberInput(attrs={'id': 'registrationPhoneNo'}))
    registrationPassword = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'id': 'registrationPassword'}))
