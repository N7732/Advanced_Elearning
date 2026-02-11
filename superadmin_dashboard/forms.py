from django import forms
from partern.models import TenantPartner
from accounts.models import User
from .models import DirectMessage

class DirectMessageForm(forms.ModelForm):
    class Meta:
        model = DirectMessage
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subject'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter message body', 'rows': 5}),
        }

class TenantPartnerForm(forms.ModelForm):
    # Form for creating/updating a TenantPartner
    
    class Meta:
        model = TenantPartner
        fields = [
            'name', 'pattern_type', 'contact_email', 'logo', 
            'start_date', 'description', 'structure_type', 
            'allow_public_registration', 'max_users', 'admin_user', 
            'active', 'is_approved_by_RDB'
        ]
        # Note: 'description' doesn't exist on TenantPartner model I saw earlier, checking model again.
        # Ah, looking at Step 42 output for partern/models.py:
        # It has: name, pattern_type, contact_email, is_approved_by_RDB, start_date, logo, end_date, active, max_users, structure_type, allow_public_registration, admin_user, created_by.
        # No 'description'. So remove it.
        
        fields = [
            'name', 'pattern_type', 'contact_email', 'logo', 
            'start_date', 'end_date', 'structure_type', 
            'allow_public_registration', 'max_users', 'admin_user', 
            'active', 'is_approved_by_RDB'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter organization name'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@example.com'}),
            'pattern_type': forms.Select(attrs={'class': 'form-select'}),
            'structure_type': forms.Select(attrs={'class': 'form-select'}),
            'max_users': forms.NumberInput(attrs={'class': 'form-control'}),
            'admin_user': forms.Select(attrs={'class': 'form-select'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['admin_user'].queryset = User.objects.all()
        self.fields['allow_public_registration'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['active'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['is_approved_by_RDB'].widget.attrs.update({'class': 'form-check-input'})
