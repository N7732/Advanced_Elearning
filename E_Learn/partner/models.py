# partner/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
from django.utils import timezone
import uuid
import os

User = settings.AUTH_USER_MODEL

def partner_logo_path(instance, filename):
    """Generate file path for partner logo"""
    ext = filename.split('.')[-1]
    filename = f"{slugify(instance.name)}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('partner_logos', filename)

def partner_document_path(instance, filename):
    """Generate file path for partner documents"""
    ext = filename.split('.')[-1]
    filename = f"{slugify(instance.partner.name)}_{instance.document_type}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('partner_documents', filename)


class Partner(models.Model):
    """
    Main Partner Model - Represents any organization/institution that partners with the platform
    Supports: Institutions, Corporate, Individual, Government
    """
    
    # Partner Types
    class PartnerType(models.TextChoices):
        INSTITUTION = 'institution', 'Educational Institution'
        CORPORATE = 'corporate', 'Corporate / Business'
        INDIVIDUAL = 'individual', 'Individual / Freelancer'
        GOVERNMENT = 'government', 'Government Agency'
        NONPROFIT = 'nonprofit', 'Non-Profit Organization'
        BOOTCAMP = 'bootcamp', 'Training Bootcamp'
    
    # Partnership Tiers
    class PartnershipTier(models.TextChoices):
        BASIC = 'basic', 'Basic Partner'
        PREMIUM = 'premium', 'Premium Partner'
        ENTERPRISE = 'enterprise', 'Enterprise Partner'
        CUSTOM = 'custom', 'Custom Agreement'
    
    # Organization Structure Types
    class StructureType(models.TextChoices):
        NONE = 'none', 'No Structure'
        DEPARTMENTAL = 'departmental', 'Departmental Only'
        UNIVERSITY = 'university', 'University Wide (with Faculties)'
        CORPORATE_HIERARCHY = 'corporate', 'Corporate Hierarchy'
        MULTI_CAMPUS = 'multi_campus', 'Multi-Campus'
    
    # Verification Status
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Verification'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'
        SUSPENDED = 'suspended', 'Suspended'
    
    # ===== BASIC INFORMATION =====
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner_id = models.CharField(max_length=50, unique=True, blank=True, 
                                  help_text="Unique partner identifier (auto-generated)")
    
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    partner_type = models.CharField(max_length=20, choices=PartnerType.choices, default=PartnerType.INSTITUTION)
    partnership_tier = models.CharField(max_length=20, choices=PartnershipTier.choices, default=PartnershipTier.BASIC)
    structure_type = models.CharField(max_length=20, choices=StructureType.choices, default=StructureType.NONE)
    
    # ===== CONTACT INFORMATION =====
    contact_email = models.EmailField(unique=True, validators=[EmailValidator()])
    alternate_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True, null=True)
    
    # ===== ADDRESS =====
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Rwanda')
    
    # ===== BRANDING & MEDIA =====
    logo = models.ImageField(upload_to=partner_logo_path, null=True, blank=True)
    banner = models.ImageField(upload_to='partner_banners/', null=True, blank=True)
    favicon = models.ImageField(upload_to='partner_favicons/', null=True, blank=True)
    brand_color_primary = models.CharField(max_length=7, default='#2563eb', help_text="Primary brand color (hex)")
    brand_color_secondary = models.CharField(max_length=7, default='#1e40af', help_text="Secondary brand color (hex)")
    
    # ===== DESCRIPTION & DETAILS =====
    short_description = models.CharField(max_length=200, blank=True)
    full_description = models.TextField(blank=True)
    established_year = models.PositiveIntegerField(null=True, blank=True)
    employee_count = models.PositiveIntegerField(null=True, blank=True)
    tax_id = models.CharField(max_length=50, blank=True, help_text="Tax/VAT identification number")
    registration_number = models.CharField(max_length=50, blank=True, help_text="Official registration number")
    
    # ===== VERIFICATION & APPROVAL =====
    verification_status = models.CharField(
        max_length=20, 
        choices=VerificationStatus.choices, 
        default=VerificationStatus.PENDING
    )
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_partners'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection if applicable")
    
    # Government/RDB approval (specific to Rwanda)
    is_approved_by_rdb = models.BooleanField(default=False, help_text="Approved by Rwanda Development Board")
    rdb_approval_number = models.CharField(max_length=50, blank=True)
    rdb_approval_date = models.DateField(null=True, blank=True)
    
    # ===== DATES & DURATION =====
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    trial_until = models.DateField(null=True, blank=True, help_text="If in trial period")
    
    # ===== STATUS FLAGS =====
    is_active = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False, help_text="Show in featured partners")
    is_public = models.BooleanField(default=True, help_text="Visible to public")
    allow_public_registration = models.BooleanField(
        default=False, 
        help_text="Allow students to register publicly without invitation"
    )
    
    # ===== USAGE LIMITS & QUOTAS =====
    max_admins = models.PositiveIntegerField(default=2, help_text="Maximum number of partner admins allowed")
    max_instructors = models.PositiveIntegerField(default=5)
    max_courses = models.PositiveIntegerField(default=10)
    max_students = models.PositiveIntegerField(default=100)
    max_storage_gb = models.PositiveIntegerField(default=5, help_text="Storage quota in GB")
    max_api_calls = models.PositiveIntegerField(default=10000, help_text="Monthly API call limit")
    
    # ===== FINANCIAL =====
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Platform commission percentage"
    )
    subscription_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Monthly subscription fee"
    )
    currency = models.CharField(max_length=3, default='RWF')
    billing_email = models.EmailField(blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    auto_renew = models.BooleanField(default=True)
    
    # ===== FEATURES & PERMISSIONS =====
    features = models.JSONField(default=dict, blank=True, help_text="JSON of enabled features")
    custom_domain = models.CharField(max_length=100, blank=True, help_text="Custom domain if allowed")
    ssl_enabled = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    white_label = models.BooleanField(default=False, help_text="Remove platform branding")
    
    # ===== METRICS & STATISTICS (Denormalized) =====
    total_admins = models.PositiveIntegerField(default=0)
    total_instructors = models.PositiveIntegerField(default=0)
    total_students = models.PositiveIntegerField(default=0)
    total_courses = models.PositiveIntegerField(default=0)
    total_enrollments = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    storage_used_mb = models.PositiveIntegerField(default=0)
    
    # ===== RELATIONSHIPS =====
    # Main admin user for this partner
    primary_admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_partner',
        help_text="Primary administrator for this partner"
    )
    
    # Partner admins (additional admins)
    admins = models.ManyToManyField(
        User,
        through='PartnerAdmin',
        related_name='partner_roles',
        blank=True
    )
    
    # Who created this partner (superadmin)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_partners'
    )
    
    # ===== TIMESTAMPS =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Partner"
        verbose_name_plural = "Partners"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['partner_type', 'is_active']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['partner_id']),
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"
    
    def save(self, *args, **kwargs):
        if not self.partner_id:
            # Generate unique partner ID: PART-YYYY-XXXX
            year = timezone.now().year
            last_partner = Partner.objects.filter(partner_id__startswith=f'PART-{year}').order_by('-partner_id').first()
            if last_partner:
                last_num = int(last_partner.partner_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.partner_id = f'PART-{year}-{new_num:04d}'
        
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Partner.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Auto-set trial end date if not set
        if not self.end_date and self.trial_until:
            self.end_date = self.trial_until
        
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if partner is currently active and within valid date range"""
        if not self.is_active:
            return False
        today = timezone.now().date()
        if self.start_date and self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True
    
    @property
    def is_trial(self):
        """Check if partner is in trial period"""
        if not self.trial_until:
            return False
        return timezone.now().date() <= self.trial_until
    
    @property
    def days_remaining(self):
        """Get days remaining in partnership/trial"""
        if not self.end_date:
            return None
        delta = self.end_date - timezone.now().date()
        return delta.days
    
    def update_stats(self):
        """Update denormalized statistics"""
        from Courses.models import Course
        from Account.models import User
        
        self.total_courses = Course.objects.filter(partner=self).count()
        self.total_admins = PartnerAdmin.objects.filter(partner=self).count()
        self.total_instructors = PartnerInstructor.objects.filter(partner=self).count()
        self.save(update_fields=[
            'total_courses', 'total_admins', 'total_instructors', 'updated_at'
        ])


class PartnerAdmin(models.Model):
    """
    Through model for partner administrators
    """
    class AdminRole(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin (Full Access)'
        CONTENT_MANAGER = 'content_manager', 'Content Manager'
        USER_MANAGER = 'user_manager', 'User Manager'
        FINANCE_MANAGER = 'finance_manager', 'Finance Manager'
        REPORT_VIEWER = 'report_viewer', 'Report Viewer'
    
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='partner_admin_relations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partner_admin_relations')
    role = models.CharField(max_length=20, choices=AdminRole.choices, default=AdminRole.SUPER_ADMIN)
    
    # Permissions (granular control)
    can_manage_instructors = models.BooleanField(default=True)
    can_manage_courses = models.BooleanField(default=True)
    can_manage_students = models.BooleanField(default=True)
    can_view_finances = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)
    can_manage_billing = models.BooleanField(default=False)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['partner', 'user']
        verbose_name = "Partner Admin"
        verbose_name_plural = "Partner Admins"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.partner.name} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        # Set permissions based on role
        if self.role == 'super_admin':
            self.can_manage_instructors = True
            self.can_manage_courses = True
            self.can_manage_students = True
            self.can_view_finances = True
            self.can_manage_settings = True
            self.can_manage_billing = True
        elif self.role == 'content_manager':
            self.can_manage_instructors = True
            self.can_manage_courses = True
            self.can_manage_students = False
        elif self.role == 'user_manager':
            self.can_manage_instructors = True
            self.can_manage_students = True
        super().save(*args, **kwargs)


class PartnerInstructor(models.Model):
    """
    Instructors belonging to a partner
    """
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='instructors')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partner_instructor_profiles')
    
    # Professional info
    bio = models.TextField(blank=True)
    expertise = models.CharField(max_length=200, blank=True)
    qualifications = models.TextField(blank=True)
    
    # Role within partner
    title = models.CharField(max_length=100, blank=True, help_text="e.g., Senior Instructor, Head of Department")
    is_primary = models.BooleanField(default=False, help_text="Primary contact instructor")
    is_featured = models.BooleanField(default=False)
    
    # Stats
    total_courses = models.PositiveIntegerField(default=0)
    total_students = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['partner', 'user']
        verbose_name = "Partner Instructor"
        verbose_name_plural = "Partner Instructors"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.partner.name}"
    
    def update_stats(self):
        from Courses.models import Course
        courses = Course.objects.filter(instructor=self.user.instructor_profile, partner=self.partner)
        self.total_courses = courses.count()
        self.save(update_fields=['total_courses'])


class Campus(models.Model):
    """
    Represents a campus or branch of a Partner organization
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='campuses')
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True, help_text="Campus code")
    
    # Location
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Rwanda')
    
    # Contact
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Head of campus
    head_of_campus = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_campuses'
    )
    
    # Metadata
    is_main_campus = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    established_date = models.DateField(null=True, blank=True)
    
    # Stats
    total_departments = models.PositiveIntegerField(default=0)
    total_students = models.PositiveIntegerField(default=0)
    total_instructors = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Campus"
        verbose_name_plural = "Campuses"
        ordering = ['partner__name', 'name']
        unique_together = ['partner', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.partner.name}"
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name).upper().replace('-', '_')
        super().save(*args, **kwargs)
    
    def update_stats(self):
        self.total_departments = self.departments.count()
        self.save(update_fields=['total_departments'])


class Faculty(models.Model):
    """
    Represents a Faculty/School within a University-type partner
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='faculties')
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    
    description = models.TextField(blank=True)
    
    # Dean/Head
    dean = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dean_of_faculties'
    )
    
    # Contact
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Stats
    total_departments = models.PositiveIntegerField(default=0)
    total_students = models.PositiveIntegerField(default=0)
    total_instructors = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    established_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Faculty"
        verbose_name_plural = "Faculties"
        ordering = ['campus__name', 'name']
        unique_together = ['campus', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.campus.name}"
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name).upper().replace('-', '_')
        super().save(*args, **kwargs)
    
    def update_stats(self):
        self.total_departments = self.departments.count()
        self.save(update_fields=['total_departments'])


class Department(models.Model):
    """
    Represents a Department within a Faculty/School
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Can belong to either a Faculty or directly to Campus (for non-university structures)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, null=True, blank=True, related_name='departments')
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, null=True, blank=True, related_name='departments')
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    
    description = models.TextField(blank=True)
    
    # Head of Department
    head_of_department = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments'
    )
    
    # Contact
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Stats
    total_students = models.PositiveIntegerField(default=0)
    total_instructors = models.PositiveIntegerField(default=0)
    total_courses = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ['name']
        indexes = [
            models.Index(fields=['faculty', 'name']),
            models.Index(fields=['campus', 'name']),
        ]
    
    def __str__(self):
        if self.faculty:
            return f"{self.name} - {self.faculty.name}"
        elif self.campus:
            return f"{self.name} - {self.campus.name}"
        return self.name
    
    def clean(self):
        """Ensure department belongs to either faculty or campus, not both"""
        if self.faculty and self.campus:
            raise models.ValidationError("Department cannot belong to both Faculty and Campus")
        if not self.faculty and not self.campus:
            raise models.ValidationError("Department must belong to either Faculty or Campus")
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.code:
            self.code = slugify(self.name).upper().replace('-', '_')
        super().save(*args, **kwargs)


class PartnerDocument(models.Model):
    """
    Documents uploaded by partners (contracts, agreements, etc.)
    """
    class DocumentType(models.TextChoices):
        CONTRACT = 'contract', 'Contract/Agreement'
        ID_PROOF = 'id_proof', 'ID Proof'
        REGISTRATION = 'registration', 'Registration Certificate'
        TAX = 'tax', 'Tax Certificate'
        LOGO = 'logo', 'Logo/Branding'
        OTHER = 'other', 'Other'
    
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    title = models.CharField(max_length=200)
    
    file = models.FileField(upload_to=partner_document_path)
    file_size = models.PositiveIntegerField(editable=False, help_text="File size in bytes")
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    expiry_date = models.DateField(null=True, blank=True, help_text="If document has expiry date")
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Partner Document"
        verbose_name_plural = "Partner Documents"
    
    def __str__(self):
        return f"{self.partner.name} - {self.get_document_type_display()}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class PartnerInvitation(models.Model):
    """
    Invitations for users to join a partner organization
    """
    class InvitationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'
    
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    
    # Role to assign when accepted
    role = models.CharField(max_length=20, choices=PartnerAdmin.AdminRole.choices, default=PartnerAdmin.AdminRole.CONTENT_MANAGER)
    
    # Invitation token
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Who sent it
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_invitations')
    
    # Status
    status = models.CharField(max_length=20, choices=InvitationStatus.choices, default=InvitationStatus.PENDING)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['partner', 'email']
        verbose_name = "Partner Invitation"
        verbose_name_plural = "Partner Invitations"
    
    def __str__(self):
        return f"Invitation for {self.email} to join {self.partner.name}"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def accept(self, user):
        """Accept invitation and create partner admin"""
        if self.is_expired:
            self.status = self.InvitationStatus.EXPIRED
            self.save()
            return False, "Invitation has expired"
        
        # Create partner admin
        PartnerAdmin.objects.create(
            partner=self.partner,
            user=user,
            role=self.role
        )
        
        self.status = self.InvitationStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.save()
        return True, "Successfully joined partner"


class PartnerActivityLog(models.Model):
    """
    Log of partner-related activities for audit
    """
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Partner Activity Log"
        verbose_name_plural = "Partner Activity Logs"
    
    def __str__(self):
        return f"{self.partner.name} - {self.action} - {self.created_at}"


class PartnerSubscription(models.Model):
    """
    Subscription/payment history for partners
    """
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='subscriptions')
    
    # Subscription period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Amount
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='RWF')
    
    # Status
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Invoice
    invoice_number = models.CharField(max_length=50, blank=True)
    invoice_file = models.FileField(upload_to='partner_invoices/', null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = "Partner Subscription"
        verbose_name_plural = "Partner Subscriptions"
    
    def __str__(self):
        return f"{self.partner.name} - {self.start_date} to {self.end_date}"
    
    @property
    def duration_months(self):
        """Calculate subscription duration in months"""
        delta = self.end_date - self.start_date
        return round(delta.days / 30, 1)