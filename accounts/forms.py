from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'password1', 'password2')
        labels = {'first_name': 'First name (optional)'}
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken. Choose another.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account already uses this email. Try signing in.')
        return email


class LoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'The username or password is incorrect. Please try again.',
    }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'contact_number',
            'preferred_accidentals', 'default_bpm',
        )
        widgets = {
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'contact_number': forms.TextInput(attrs={'autocomplete': 'tel', 'type': 'tel'}),
            'default_bpm': forms.NumberInput(attrs={'min': 40, 'max': 240}),
        }
        labels = {'contact_number': 'Contact number (optional)'}
        help_texts = {
            'preferred_accidentals': 'Your preferred chord spelling for future chart tools.',
            'default_bpm': 'Choose 40–240 BPM. This will be used by the practice reader.',
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('An account already uses this email. Choose another.')
        return email
