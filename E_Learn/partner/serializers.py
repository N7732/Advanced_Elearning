# partner/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import *
import uuid

User = get_user_model()

# ==================== HELPER SERIALIZERS ====================

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serializers"""
    full_name = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source='picture_profile', read_only=True, default=None)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'avatar']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class PartnerDocumentSerializer(serializers.ModelSerializer):
    """Serializer for partner documents"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PartnerDocument
        fields = [
            'id', 'partner', 'document_type', 'title', 'file', 'file_url',
            'file_size', 'uploaded_by', 'uploaded_by_name', 'uploaded_at',
            'expiry_date', 'is_verified', 'verified_by', 'verified_by_name',
            'verified_at', 'notes'
        ]
        read_only_fields = ['id', 'file_size', 'uploaded_at', 'verified_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def validate_file(self, value):
        # Validate file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        # Validate file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only PDF, JPEG, and PNG files are allowed")
        
        return value


class PartnerActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for partner activity logs"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = PartnerActivityLog
        fields = ['id', 'partner', 'user', 'user_name', 'action', 'details', 'ip_address', 'created_at']
        read_only_fields = ['created_at']


class PartnerSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for partner subscriptions"""
    duration_months = serializers.FloatField(read_only=True)
    
    class Meta:
        model = PartnerSubscription
        fields = [
            'id', 'partner', 'start_date', 'end_date', 'amount', 'currency',
            'is_paid', 'payment_date', 'payment_method', 'transaction_id',
            'invoice_number', 'invoice_file', 'notes', 'created_at', 'duration_months'
        ]
        read_only_fields = ['created_at']


class PartnerInvitationSerializer(serializers.ModelSerializer):
    """Serializer for partner invitations"""
    invited_by_name = serializers.CharField(source='invited_by.get_full_name', read_only=True)
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PartnerInvitation
        fields = [
            'id', 'partner', 'partner_name', 'email', 'role', 'token',
            'invited_by', 'invited_by_name', 'status', 'created_at',
            'expires_at', 'accepted_at', 'is_expired'
        ]
        read_only_fields = ['id', 'token', 'created_at', 'accepted_at']


class PartnerAdminSerializer(serializers.ModelSerializer):
    """Serializer for partner admins"""
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    
    class Meta:
        model = PartnerAdmin
        fields = [
            'id', 'partner', 'partner_name', 'user', 'user_id', 'role',
            'can_manage_instructors', 'can_manage_courses', 'can_manage_students',
            'can_view_finances', 'can_manage_settings', 'can_manage_billing',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PartnerInstructorSerializer(serializers.ModelSerializer):
    """Serializer for partner instructors"""
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    
    class Meta:
        model = PartnerInstructor
        fields = [
            'id', 'partner', 'partner_name', 'user', 'user_id', 'bio',
            'expertise', 'qualifications', 'title', 'is_primary', 'is_featured',
            'total_courses', 'total_students', 'average_rating', 'is_active',
            'joined_at'
        ]
        read_only_fields = ['total_courses', 'total_students', 'average_rating', 'joined_at']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for departments"""
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    head_name = serializers.CharField(source='head_of_department.get_full_name', read_only=True)
    
    class Meta:
        model = Department
        fields = [
            'id', 'faculty', 'faculty_name', 'campus', 'campus_name',
            'name', 'code', 'description', 'head_of_department', 'head_name',
            'contact_email', 'contact_phone', 'total_students', 'total_instructors',
            'total_courses', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at', 'total_students', 'total_instructors', 'total_courses']
    
    def validate(self, data):
        """Ensure department belongs to either faculty or campus, not both"""
        faculty = data.get('faculty')
        campus = data.get('campus')
        
        if faculty and campus:
            raise serializers.ValidationError("Department cannot belong to both Faculty and Campus")
        if not faculty and not campus:
            raise serializers.ValidationError("Department must belong to either Faculty or Campus")
        
        return data


class FacultySerializer(serializers.ModelSerializer):
    """Serializer for faculties"""
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    dean_name = serializers.CharField(source='dean.get_full_name', read_only=True)
    departments = DepartmentSerializer(many=True, read_only=True)
    departments_count = serializers.IntegerField(source='departments.count', read_only=True)
    
    class Meta:
        model = Faculty
        fields = [
            'id', 'campus', 'campus_name', 'name', 'code', 'description',
            'dean', 'dean_name', 'contact_email', 'contact_phone',
            'total_departments', 'total_students', 'total_instructors',
            'departments', 'departments_count', 'is_active', 'established_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at', 'total_departments']


class CampusSerializer(serializers.ModelSerializer):
    """Serializer for campuses"""
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    head_name = serializers.CharField(source='head_of_campus.get_full_name', read_only=True)
    faculties = FacultySerializer(many=True, read_only=True)
    departments = DepartmentSerializer(many=True, read_only=True)
    faculties_count = serializers.IntegerField(source='faculties.count', read_only=True)
    departments_count = serializers.IntegerField(source='departments.count', read_only=True)
    
    class Meta:
        model = Campus
        fields = [
            'id', 'partner', 'partner_name', 'name', 'code',
            'address_line1', 'address_line2', 'city', 'state_province',
            'postal_code', 'country', 'contact_email', 'contact_phone',
            'head_of_campus', 'head_name', 'is_main_campus', 'is_active',
            'established_date', 'total_departments', 'total_students',
            'total_instructors', 'faculties', 'faculties_count',
            'departments', 'departments_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']


# ==================== MAIN PARTNER SERIALIZERS ====================

class PartnerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for partner list views (for performance)"""
    partner_type_display = serializers.CharField(source='get_partner_type_display', read_only=True)
    tier_display = serializers.CharField(source='get_partnership_tier_display', read_only=True)
    status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    primary_admin_name = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    is_valid = serializers.BooleanField(read_only=True)
    is_trial = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Partner
        fields = [
            'id', 'partner_id', 'name', 'slug', 'partner_type', 'partner_type_display',
            'partnership_tier', 'tier_display', 'verification_status', 'status_display',
            'logo', 'logo_url', 'short_description', 'city', 'country',
            'is_active', 'is_featured', 'is_valid', 'is_trial', 'days_remaining',
            'total_courses', 'total_students', 'average_rating',
            'primary_admin', 'primary_admin_name', 'created_at'
        ]
    
    def get_primary_admin_name(self, obj):
        if obj.primary_admin:
            return obj.primary_admin.get_full_name() or obj.primary_admin.username
        return None
    
    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None


class PartnerDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single partner view"""
    partner_type_display = serializers.CharField(source='get_partner_type_display', read_only=True)
    tier_display = serializers.CharField(source='get_partnership_tier_display', read_only=True)
    structure_display = serializers.CharField(source='get_structure_type_display', read_only=True)
    status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    
    # Nested objects
    primary_admin = UserBasicSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    verified_by = UserBasicSerializer(read_only=True)
    
    # Related data
    campuses = CampusSerializer(many=True, read_only=True)
    admins = PartnerAdminSerializer(many=True, read_only=True, source='partner_admin_relations')
    instructors = PartnerInstructorSerializer(many=True, read_only=True)
    documents = PartnerDocumentSerializer(many=True, read_only=True)
    recent_activity = serializers.SerializerMethodField()
    
    # Computed fields
    logo_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()
    is_valid = serializers.BooleanField(read_only=True)
    is_trial = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Partner
        fields = [
            # Identifiers
            'id', 'partner_id', 'name', 'slug',
            
            # Type & Classification
            'partner_type', 'partner_type_display',
            'partnership_tier', 'tier_display',
            'structure_type', 'structure_display',
            'verification_status', 'status_display',
            
            # Contact
            'contact_email', 'alternate_email', 'contact_phone', 'alternate_phone',
            'website',
            
            # Address
            'address_line1', 'address_line2', 'city', 'state_province',
            'postal_code', 'country',
            
            # Branding
            'logo', 'logo_url', 'banner', 'banner_url', 'favicon', 'favicon_url',
            'brand_color_primary', 'brand_color_secondary',
            
            # Description
            'short_description', 'full_description',
            'established_year', 'employee_count', 'tax_id', 'registration_number',
            
            # Verification
            'verification_status', 'verified_by', 'verified_at', 'rejection_reason',
            'is_approved_by_rdb', 'rdb_approval_number', 'rdb_approval_date',
            
            # Dates
            'start_date', 'end_date', 'trial_until',
            
            # Status
            'is_active', 'is_featured', 'is_public', 'allow_public_registration',
            'is_valid', 'is_trial', 'days_remaining',
            
            # Quotas & Limits
            'max_admins', 'max_instructors', 'max_courses', 'max_students',
            'max_storage_gb', 'max_api_calls', 'usage_percentage',
            
            # Financial
            'commission_rate', 'subscription_fee', 'currency',
            'billing_email', 'payment_method', 'auto_renew',
            
            # Features
            'features', 'custom_domain', 'ssl_enabled', 'api_access', 'white_label',
            
            # Statistics
            'total_admins', 'total_instructors', 'total_students',
            'total_courses', 'total_enrollments', 'total_revenue',
            'average_rating', 'storage_used_mb',
            
            # Relationships
            'primary_admin', 'created_by', 'campuses', 'admins',
            'instructors', 'documents', 'recent_activity',
            
            # Timestamps
            'created_at', 'updated_at', 'last_activity'
        ]
        read_only_fields = [
            'id', 'partner_id', 'slug', 'created_at', 'updated_at',
            'total_admins', 'total_instructors', 'total_students',
            'total_courses', 'total_enrollments', 'total_revenue',
            'average_rating', 'storage_used_mb'
        ]
    
    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None
    
    def get_banner_url(self, obj):
        request = self.context.get('request')
        if obj.banner and request:
            return request.build_absolute_uri(obj.banner.url)
        return None
    
    def get_favicon_url(self, obj):
        request = self.context.get('request')
        if obj.favicon and request:
            return request.build_absolute_uri(obj.favicon.url)
        return None
    
    def get_usage_percentage(self, obj):
        """Calculate usage percentage for quotas"""
        if obj.max_students > 0:
            student_usage = (obj.total_students / obj.max_students) * 100
        else:
            student_usage = 0
            
        if obj.max_storage_gb > 0:
            storage_usage = (obj.storage_used_mb / (obj.max_storage_gb * 1024)) * 100
        else:
            storage_usage = 0
        
        return {
            'students': round(student_usage, 1),
            'storage': round(storage_usage, 1),
            'courses': round((obj.total_courses / obj.max_courses) * 100 if obj.max_courses > 0 else 0, 1),
            'instructors': round((obj.total_instructors / obj.max_instructors) * 100 if obj.max_instructors > 0 else 0, 1)
        }
    
    def get_recent_activity(self, obj):
        """Get 5 most recent activity logs"""
        logs = obj.activity_logs.all()[:5]
        return PartnerActivityLogSerializer(logs, many=True, context=self.context).data


class PartnerCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating partners"""
    primary_admin_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='primary_admin',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Partner
        fields = [
            'name', 'partner_type', 'partnership_tier', 'structure_type',
            'contact_email', 'alternate_email', 'contact_phone', 'alternate_phone',
            'website', 'address_line1', 'address_line2', 'city',
            'state_province', 'postal_code', 'country',
            'short_description', 'full_description',
            'established_year', 'employee_count', 'tax_id', 'registration_number',
            'start_date', 'end_date', 'trial_until',
            'is_public', 'allow_public_registration',
            'max_admins', 'max_instructors', 'max_courses',
            'max_students', 'max_storage_gb', 'max_api_calls',
            'commission_rate', 'subscription_fee', 'currency',
            'billing_email', 'payment_method', 'auto_renew',
            'features', 'custom_domain', 'ssl_enabled', 'api_access', 'white_label',
            'primary_admin_id'
        ]
    
    def validate_contact_email(self, value):
        """Check if email is unique (excluding current instance)"""
        if self.instance:
            if Partner.objects.exclude(pk=self.instance.pk).filter(contact_email=value).exists():
                raise serializers.ValidationError("A partner with this email already exists")
        else:
            if Partner.objects.filter(contact_email=value).exists():
                raise serializers.ValidationError("A partner with this email already exists")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Validate dates
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        
        if data.get('trial_until') and data.get('start_date'):
            if data['trial_until'] < data['start_date']:
                raise serializers.ValidationError("Trial end date must be after start date")
        
        # Validate quotas
        if data.get('max_admins', 0) < 1:
            raise serializers.ValidationError("max_admins must be at least 1")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # Set created_by to current user (superadmin)
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        partner = Partner.objects.create(**validated_data)
        
        # Log activity
        PartnerActivityLog.objects.create(
            partner=partner,
            user=request.user if request else None,
            action='CREATE',
            details={'method': 'api', 'data': validated_data},
            ip_address=request.META.get('REMOTE_ADDR') if request else None
        )
        
        return partner
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        
        # Track changes for audit
        changes = {}
        for field, value in validated_data.items():
            if hasattr(instance, field):
                old_value = getattr(instance, field)
                if old_value != value:
                    changes[field] = {'old': str(old_value), 'new': str(value)}
        
        # Update instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Log activity if there were changes
        if changes and request:
            PartnerActivityLog.objects.create(
                partner=instance,
                user=request.user,
                action='UPDATE',
                details={'changes': changes},
                ip_address=request.META.get('REMOTE_ADDR')
            )
        
        return instance


class PartnerVerificationSerializer(serializers.Serializer):
    """Serializer for partner verification workflow"""
    action = serializers.ChoiceField(choices=['verify', 'reject', 'suspend'])
    reason = serializers.CharField(required=False, allow_blank=True)
    rdb_approval_number = serializers.CharField(required=False, allow_blank=True)
    rdb_approval_date = serializers.DateField(required=False)
    
    def validate(self, data):
        if data['action'] in ['reject', 'suspend'] and not data.get('reason'):
            raise serializers.ValidationError(f"Reason is required for {data['action']} action")
        return data
    
    def save(self, partner):
        request = self.context.get('request')
        action = self.validated_data['action']
        
        if action == 'verify':
            partner.verification_status = Partner.VerificationStatus.VERIFIED
            partner.verified_by = request.user if request else None
            partner.verified_at = timezone.now()
            partner.is_active = True
            
            if self.validated_data.get('rdb_approval_number'):
                partner.is_approved_by_rdb = True
                partner.rdb_approval_number = self.validated_data['rdb_approval_number']
                partner.rdb_approval_date = self.validated_data.get('rdb_approval_date', timezone.now().date())
        
        elif action == 'reject':
            partner.verification_status = Partner.VerificationStatus.REJECTED
            partner.rejection_reason = self.validated_data['reason']
            partner.is_active = False
        
        elif action == 'suspend':
            partner.verification_status = Partner.VerificationStatus.SUSPENDED
            partner.rejection_reason = self.validated_data['reason']
            partner.is_active = False
        
        partner.save()
        
        # Log activity
        PartnerActivityLog.objects.create(
            partner=partner,
            user=request.user if request else None,
            action=action.upper(),
            details={'reason': self.validated_data.get('reason', '')},
            ip_address=request.META.get('REMOTE_ADDR') if request else None
        )
        
        return partner


class PartnerStatsSerializer(serializers.Serializer):
    """Serializer for partner statistics dashboard"""
    overview = serializers.DictField()
    trends = serializers.DictField()
    top_courses = serializers.ListField()
    recent_activity = serializers.ListField()
    usage = serializers.DictField()


# ==================== INVITATION SERIALIZERS ====================

class PartnerInvitationCreateSerializer(serializers.Serializer):
    """Serializer for creating multiple invitations"""
    emails = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False,
        max_length=20
    )
    role = serializers.ChoiceField(choices=PartnerAdmin.AdminRole.choices, default=PartnerAdmin.AdminRole.CONTENT_MANAGER)
    message = serializers.CharField(required=False, allow_blank=True)
    
    def create(self, validated_data):
        partner = self.context['partner']
        request = self.context.get('request')
        
        invitations = []
        for email in validated_data['emails']:
            # Check if already invited
            existing = PartnerInvitation.objects.filter(
                partner=partner,
                email=email,
                status__in=['pending', 'accepted']
            ).first()
            
            if existing:
                continue
            
            invitation = PartnerInvitation.objects.create(
                partner=partner,
                email=email,
                role=validated_data['role'],
                invited_by=request.user if request else None
            )
            invitations.append(invitation)
        
        return invitations