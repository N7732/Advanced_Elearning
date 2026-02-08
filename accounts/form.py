from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Learner, Instructor, AccountProfile
from partern.models import TenantPartner

User = get_user_model()

class LearnerRegistrationForm(UserCreationForm):
    """Form for learner registration"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    terms_agreed = forms.BooleanField(required=True)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
        
    def save(self, commit=True):
        """
        Saves the form data and sets the username to the email address.
        
        Args:
            commit (bool): whether to save the user to the database.
        
        Returns:
            User: The created user instance.
        """
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user
        
    def __init__(self, *args, **kwargs):
        """
        Initializes the form and adds Bootstrap class to fields.
        """
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'terms_agreed':
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class InstructorRegistrationForm(UserCreationForm):
    """Form for instructor registration"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    professional_title = forms.CharField(max_length=100, required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    expertise_areas = forms.CharField(widget=forms.HiddenInput, required=False)
    experience_level = forms.CharField(max_length=20, required=False)
    linkedin_profile = forms.URLField(required=False)
    terms_agreed = forms.BooleanField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        
    def __init__(self, *args, **kwargs):
        """
        Initializes the form and adds Bootstrap class to fields.
        """
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'terms_agreed':
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class LearnerForm(forms.ModelForm):
    """Form for editing learner profile"""
    class Meta:
        model = Learner
        fields = ['phone_number', 'birth_date']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class InstructorForm(forms.ModelForm):
    """Form for editing instructor profile"""
    class Meta:
        model = Instructor
        fields = ['phone_number', 'bio', 'specialization', 'profile_picture']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class AccountProfileForm(forms.ModelForm):
    """Form for editing extended account profile"""
    class Meta:
        model = AccountProfile
        fields = ['bio', 'profile_picture', 'address', 'city', 'country']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }

class LoginForm(forms.Form):
    """Form for user login"""
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
