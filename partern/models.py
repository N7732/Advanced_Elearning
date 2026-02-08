from django.db import models
from django.conf import settings

class TenantPartner(models.Model):
    """
    Represents a partner organization (institution, corporate, or individual)
    that can have their own admin and manage students, courses, and instructors
    """
    PATTERN_TYPE = [
        ('institution', 'Institution'),
        ('corporate', 'Corporate'),
        ('individual', 'Individual'),
        ('government', 'Government'),
    ]
    Structure_type= [
    ('None', 'None'),
    ("Departmental", 'Departmental only'),
    ("Unversity", 'University wide'),
    ]
    name = models.CharField(max_length=100, help_text="Partner organization name")
    pattern_type = models.CharField(max_length=20, choices=PATTERN_TYPE)
    contact_email = models.EmailField(unique=True)
    is_approved_by_RDB= models.BooleanField(default=True, help_text="Approved by RDB")
    start_date = models.DateField()
    logo = models.ImageField(upload_to='partner_logos/', null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=False, help_text="Partner is active and approved")
    max_users = models.PositiveIntegerField(default=5, help_text="Maximum number of students allowed")
    structure_type = models.CharField(max_length=20, choices=Structure_type, default='None')
    allow_public_registration = models.BooleanField(default=False, help_text="Allow students to register publicly without invitation")
    
    # Link to partner admin user
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='managed_partners',
        help_text="Partner admin who manages this organization"
    )
    
    # Super admin who created/approved this partner
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_partners',
        help_text="Super admin who created this partner"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tenant Partner"
        verbose_name_plural = "Tenant Partners"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_pattern_type_display()})"
    
    @property
    def is_active(self):
        """Check if partner is currently active"""
        from django.utils import timezone
        if not self.active:
            return False
        if self.end_date and self.end_date < timezone.now().date():
            return False
        return True

class Campus(models.Model):
    """
    Represents a campus or branch of a TenantPartner organization
    """
    partner = models.ForeignKey(
        TenantPartner,
        on_delete=models.CASCADE,
        related_name='campuses',
        help_text="Partner organization this campus belongs to"
    )
    name = models.CharField(max_length=100, help_text="Campus name")
    location = models.CharField(max_length=200, blank=True, help_text="Campus location/address")
    contact_number = models.CharField(max_length=20, blank=True, help_text="Campus contact phone number")
    created_at = models.DateTimeField(auto_now_add=True)
    Head_of_campus = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campus_head',
        help_text="Head of this campus"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Campus"
        verbose_name_plural = "Campuses"
        ordering = ['partner__name', 'name']

    def __str__(self):
        return f"{self.name} - {self.partner.name}"
    
class Schools(models.Model):
    """
    Represents a school or department within a TenantPartner organization
    """
    campus= models.ForeignKey(
        Campus,
        on_delete=models.CASCADE,
        related_name='schools',
        help_text="Campus this school/department belongs to"
    )
    name = models.CharField(max_length=100, help_text="School/Department name")
    description = models.TextField(max_length=100,blank=True, help_text="Brief description of the school/department")
    Dean = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='school_dean',
        help_text="Dean of this school/department"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"
        ordering = ['campus__partner__name', 'name']

    def __str__(self):
        return f"{self.name} - {self.campus.partner.name}"
    
class Department(models.Model):
    """
    Represents a department within a school of a TenantPartner organization
    """
    school = models.ForeignKey(
        Schools,
        on_delete=models.CASCADE,
        related_name='departments',
        help_text="School this department belongs to"
    )
    name = models.CharField(max_length=100, help_text="Department name")
    description = models.TextField(max_length=100, blank=True, help_text="Brief description of the department")
    Head_of_department = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='department_head',
        help_text="Head of this department"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ['school__name', 'name']

    def __str__(self):
        return f"{self.name} - {self.school.name}"