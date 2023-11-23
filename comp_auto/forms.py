from django import forms
from django.contrib.auth.models import User
from .models import UserResponse,UploadedFile,AddMoreResponse

class RegistrationForm(forms.Form):
    registrationUsername = forms.CharField(label='Username', widget=forms.TextInput(attrs={'id': 'registrationUsername'}))
    registrationEmail = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'id': 'registrationEmail'}))
    # registrationPhoneNo = forms.CharField(label='Phone Number', widget=forms.NumberInput(attrs={'id': 'registrationPhoneNo'}))
    registrationPassword = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'id': 'registrationPassword'}))

class UserResponseForm(forms.ModelForm):
    class Meta:
        model = UserResponse
        exclude=['user']
        fields = ['compliance_type', 'audit_observations', 'recommandations']

    def __init__(self, *args, **kwargs):
        super(UserResponseForm, self).__init__(*args, **kwargs)
        self.fields['compliance_type'].widget = forms.RadioSelect(choices=UserResponse.COMPLIANCE_CHOICES)

class AnotherUserResponseForm(forms.ModelForm):
    class Meta:
        model = AddMoreResponse
        exclude = ['user']
        fields = ['title', 'Summary', 'compliance_type', 'audit_observations', 'recommandations']

    def __init__(self, *args, **kwargs):
        super(AnotherUserResponseForm, self).__init__(*args, **kwargs)


class UploadFileForm(forms.ModelForm):
    class Meta:
        model=UploadedFile
        fields=['file']

