import uuid
from django.db import models
from django.conf import settings
# from django import uuid # Remove incorrect import
# from django import partern # Remove incorrect import


class Membership(models.Model):
    CONTEXT_CHOICES = (
        ('PLATFORM', 'Platform'),
        ('PARTNER', 'Partner'),
    )

    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('INSTRUCTOR', 'Instructor'),
        ('ADMIN', 'Admin'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    context_type = models.CharField(max_length=10, choices=CONTEXT_CHOICES)
    partner = models.ForeignKey(
        'partern.TenantPartner',  # Corrected app name
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'context_type', 'partner')

    def __str__(self):
        return f"{self.user} | {self.context_type} | {self.role}"


class Invitation(models.Model):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('INSTRUCTOR', 'Instructor'),
        ('ADMIN', 'Admin'),
    )

    email = models.EmailField()
    partner = models.ForeignKey('partern.TenantPartner', on_delete=models.CASCADE) # Corrected app name
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} → {self.partner.name}"
