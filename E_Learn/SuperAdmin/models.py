# superadmin/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class GlobalSetting(models.Model):
    """Global system settings - only one instance should exist"""
    site_name = models.CharField(max_length=100, default="BlueLearn")
    site_description = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Branding
    site_logo = models.ImageField(upload_to='site_assets/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site_assets/', blank=True, null=True)
    login_background = models.ImageField(upload_to='site_assets/', blank=True, null=True)
    
    # System Settings
    maintenance_mode = models.BooleanField(default=False)
    allow_registrations = models.BooleanField(default=True)
    require_email_verification = models.BooleanField(default=True)
    
    # Security
    max_login_attempts = models.PositiveIntegerField(default=5)
    session_timeout_minutes = models.PositiveIntegerField(default=30)
    
    # Defaults
    default_user_role = models.CharField(max_length=20, default='learner', 
                                        choices=(
                                            ('learner', 'Learner'),
                                            ('instructor', 'Instructor'),
                                        ))
    
    # Meta
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Global Setting"
        verbose_name_plural = "Global Settings"

    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and GlobalSetting.objects.exists():
            # Update existing instead of creating new
            existing = GlobalSetting.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)


class SuperAdmin(models.Model):
    """Extended profile for superadmin users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='superadmin_profile')
    
    # Personal info
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True, default="Administration")
    
    # Permissions flags
    can_manage_admins = models.BooleanField(default=True)
    can_manage_instructors = models.BooleanField(default=True)
    can_manage_partners = models.BooleanField(default=True)
    can_manage_courses = models.BooleanField(default=True)
    can_manage_system = models.BooleanField(default=True)
    can_view_audit_logs = models.BooleanField(default=True)
    
    # Activity
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Super Admin"
        verbose_name_plural = "Super Admins"
    
    def __str__(self):
        return f"Super Admin: {self.user.get_full_name() or self.user.username}"
    
    @property
    def has_full_access(self):
        """Check if superadmin has all permissions"""
        return all([
            self.can_manage_admins,
            self.can_manage_instructors,
            self.can_manage_partners,
            self.can_manage_courses,
            self.can_manage_system,
            self.can_view_audit_logs
        ])


class Admin(models.Model):
    """Regular admin users managed by superadmin"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    
    # Personal info
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100, blank=True)
    
    # Admin type
    ADMIN_TYPES = (
        ('content', 'Content Admin'),
        ('user', 'User Admin'),
        ('support', 'Support Admin'),
        ('finance', 'Finance Admin'),
        ('full', 'Full Admin'),
    )
    admin_type = models.CharField(max_length=20, choices=ADMIN_TYPES, default='content')
    
    # Permissions (set based on admin_type)
    can_manage_courses = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_manage_partners = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    can_manage_finances = models.BooleanField(default=False)
    can_moderate_content = models.BooleanField(default=False)
    
    # Managed by
    created_by = models.ForeignKey(SuperAdmin, on_delete=models.SET_NULL, null=True, related_name='created_admins')
    
    # Status
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Admin"
        verbose_name_plural = "Admins"
    
    def __str__(self):
        return f"Admin: {self.user.get_full_name() or self.user.username} - {self.get_admin_type_display()}"
    
    def set_permissions_from_type(self):
        """Set permissions based on admin type"""
        if self.admin_type == 'full':
            self.can_manage_courses = True
            self.can_manage_users = True
            self.can_manage_partners = True
            self.can_view_reports = True
            self.can_manage_finances = True
            self.can_moderate_content = True
        elif self.admin_type == 'content':
            self.can_manage_courses = True
            self.can_moderate_content = True
            self.can_view_reports = True
        elif self.admin_type == 'user':
            self.can_manage_users = True
            self.can_view_reports = True
        elif self.admin_type == 'support':
            self.can_moderate_content = True
            self.can_view_reports = True
        elif self.admin_type == 'finance':
            self.can_view_reports = True
            self.can_manage_finances = True
        
        self.save(update_fields=[
            'can_manage_courses', 'can_manage_users', 'can_manage_partners',
            'can_view_reports', 'can_manage_finances', 'can_moderate_content'
        ])


class IndependentInstructor(models.Model):
    """Instructors who are not affiliated with a partner"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='independent_instructor_profile')
    
    # Professional info
    bio = models.TextField(blank=True)
    expertise = models.CharField(max_length=200, blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(SuperAdmin, on_delete=models.SET_NULL, null=True, related_name='verified_instructors')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Documents
    id_proof = models.FileField(upload_to='instructor_docs/', blank=True, null=True)
    qualification_docs = models.FileField(upload_to='instructor_docs/', blank=True, null=True)
    
    # Commission/Payment
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=70,
                                               help_text="Percentage of course revenue instructor receives")
    payment_email = models.EmailField(blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    rejection_reason = models.TextField(blank=True, help_text="If rejected, why")
    
    # Stats
    total_courses = models.PositiveIntegerField(default=0)
    total_students = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Meta
    created_by = models.ForeignKey(SuperAdmin, on_delete=models.SET_NULL, null=True, related_name='created_instructors')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Independent Instructor"
        verbose_name_plural = "Independent Instructors"
    
    def __str__(self):
        return f"Instructor: {self.user.get_full_name() or self.user.username}"
    
    def update_stats(self):
        from Courses.models import Course
        courses = Course.objects.filter(instructor=self.user.instructor_profile)
        self.total_courses = courses.count()
        # Add more stats calculation as needed
        self.save(update_fields=['total_courses'])


class Partner(models.Model):
    """Partner organizations managed by superadmin"""
    PARTNER_TYPES = (
        ('company', 'Company'),
        ('educational', 'Educational Institution'),
        ('bootcamp', 'Bootcamp'),
        ('nonprofit', 'Non-Profit'),
        ('government', 'Government'),
    )
    
    # Basic info
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPES, default='company')
    
    # Contact
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    address = models.TextField()
    
    # Branding
    logo = models.ImageField(upload_to='partner_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='partner_banners/', blank=True, null=True)
    description = models.TextField(blank=True)
    
    # Admin user(s) for this partner
    admin_users = models.ManyToManyField(User, related_name='partner_admins', blank=True,
                                        help_text="Users who can manage this partner's content")
    
    # Commission/Payment
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50,
                                               help_text="Percentage of revenue partner receives")
    billing_email = models.EmailField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    
    # Settings
    max_instructors = models.PositiveIntegerField(default=5, help_text="Maximum instructors allowed")
    max_courses = models.PositiveIntegerField(default=10, help_text="Maximum courses allowed")
    allow_own_branding = models.BooleanField(default=True, help_text="Can use own logo/branding")
    
    # Status
    is_active = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(SuperAdmin, on_delete=models.SET_NULL, null=True, related_name='verified_partners')
    
    # Stats
    total_instructors = models.PositiveIntegerField(default=0)
    total_courses = models.PositiveIntegerField(default=0)
    total_enrollments = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Meta
    created_by = models.ForeignKey(SuperAdmin, on_delete=models.SET_NULL, null=True, related_name='created_partners')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Partner"
        verbose_name_plural = "Partners"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def update_stats(self):
        from Courses.models import Course
        self.total_courses = Course.objects.filter(partner=self).count()
        # Add more stats as needed
        self.save(update_fields=['total_courses'])


class PartnerInstructor(models.Model):
    """Instructors belonging to a partner organization"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='partner_instructor_profile')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='instructors')
    
    # Professional info
    bio = models.TextField(blank=True)
    expertise = models.CharField(max_length=200, blank=True)
    
    # Role within partner
    role = models.CharField(max_length=100, blank=True, help_text="e.g., Senior Instructor, Head of Department")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False, help_text="Primary contact for partner")
    
    # Stats
    total_courses = models.PositiveIntegerField(default=0)
    total_students = models.PositiveIntegerField(default=0)
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('partner', 'user')
        verbose_name = "Partner Instructor"
        verbose_name_plural = "Partner Instructors"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.partner.name}"


class PlatformFeature(models.Model):
    """Toggle platform features on/off"""
    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=100, unique=True, help_text="Feature code used in code")
    description = models.TextField(blank=True)
    
    is_enabled = models.BooleanField(default=True)
    
    # Feature settings as JSON
    settings = models.JSONField(default=dict, blank=True, 
                               help_text="JSON configuration for the feature")
    
    # Which user types can access
    accessible_by = models.JSONField(default=list, blank=True,
                                   help_text="List of user types: ['learner', 'instructor', 'partner', 'admin']")
    
    updated_by = models.ForeignKey(SuperAdmin, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {'Enabled' if self.is_enabled else 'Disabled'}"


class SystemAnnouncement(models.Model):
    """System-wide announcements for all users"""
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Targeting
    target_roles = models.JSONField(default=list, help_text="['learner', 'instructor', 'partner', 'admin']")
    
    # Display settings
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    dismissible = models.BooleanField(default=True)
    
    # Who created it
    created_by = models.ForeignKey(SuperAdmin, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_date <= now <= self.end_date


class Notification(models.Model):
    """Notifications for users"""
    NOTIFICATION_TYPES = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info')
    
    # Link to related object (optional)
    target_url = models.CharField(max_length=500, blank=True)
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class DirectMessage(models.Model):
    """Direct messages between users"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='replies')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username}: {self.subject}"
    
    def mark_as_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class AuditLog(models.Model):
    """Track all important actions in the system"""
    ACTION_TYPES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('verify', 'Verify'),
        ('reject', 'Reject'),
        ('suspend', 'Suspend'),
        ('activate', 'Activate'),
        ('payment', 'Payment'),
        ('export', 'Export'),
        ('import', 'Import'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    username = models.CharField(max_length=150, blank=True, help_text="Username at time of action")
    
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    action_description = models.CharField(max_length=255)
    
    target_model = models.CharField(max_length=100)
    target_id = models.PositiveIntegerField()
    target_repr = models.CharField(max_length=255, blank=True, help_text="String representation of target")
    
    # Before/after for updates
    changes = models.JSONField(default=dict, blank=True, help_text="Changes made (for update actions)")
    
    # Request info
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Additional data
    details = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['target_model', 'target_id']),
        ]

    def __str__(self):
        return f"{self.user or 'System'} - {self.action} - {self.created_at}"
    
    def save(self, *args, **kwargs):
        if self.user and not self.username:
            self.username = self.user.username
        super().save(*args, **kwargs)


class SystemReport(models.Model):
    """Pre-generated system reports"""
    REPORT_TYPES = (
        ('users', 'Users Report'),
        ('courses', 'Courses Report'),
        ('revenue', 'Revenue Report'),
        ('partners', 'Partners Report'),
        ('engagement', 'Engagement Report'),
        ('custom', 'Custom Report'),
    )
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    # Report data (stored as JSON)
    data = models.JSONField(default=dict)
    
    # Parameters used to generate
    parameters = models.JSONField(default=dict)
    
    # File export (if any)
    exported_file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    # Who generated it
    generated_by = models.ForeignKey(SuperAdmin, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # Date range
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.generated_at.date()}"


class BackupRecord(models.Model):
    """Track system backups"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    name = models.CharField(max_length=200)
    backup_type = models.CharField(max_length=20, choices=(
        ('full', 'Full Backup'),
        ('database', 'Database Only'),
        ('media', 'Media Files Only'),
    ))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    file_path = models.CharField(max_length=500, blank=True)
    file_size_mb = models.PositiveIntegerField(default=0)
    
    # Metadata
    includes_media = models.BooleanField(default=True)
    includes_database = models.BooleanField(default=True)
    
    # Who triggered it
    triggered_by = models.ForeignKey(SuperAdmin, on_delete=models.SET_NULL, null=True)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error info
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.name} - {self.status}"