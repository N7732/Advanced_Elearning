# superadmin/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import *
import json

User = get_user_model()

# ==================== User Related Serializers ====================

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serializers"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'is_active']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class SuperAdminSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    
    class Meta:
        model = SuperAdmin
        fields = '__all__'
        read_only_fields = ['created_at', 'last_activity']


class SuperAdminCreateSerializer(serializers.Serializer):
    """Create a new superadmin with user account"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        # Create user
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_staff=True,
            is_superuser=True  # Django superuser
        )
        user.set_password(validated_data['password'])
        user.save()
        
        # Create superadmin profile
        superadmin = SuperAdmin.objects.create(
            user=user,
            phone=validated_data.get('phone', ''),
            department=validated_data.get('department', 'Administration')
        )
        
        return superadmin


# ==================== Admin Management ====================

class AdminSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = Admin
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_login']
    
    def validate(self, data):
        # Set permissions based on admin_type if provided
        if 'admin_type' in data and not self.instance:
            # We'll handle this in create/update
            pass
        return data
    
    def create(self, validated_data):
        user = validated_data.pop('user')
        admin_type = validated_data.get('admin_type', 'content')
        
        admin = Admin.objects.create(user=user, **validated_data)
        admin.set_permissions_from_type()  # This will set permissions based on type
        return admin


class AdminCreateSerializer(serializers.Serializer):
    """Create a new admin with user account"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField()
    position = serializers.CharField(required=False, allow_blank=True)
    admin_type = serializers.ChoiceField(choices=Admin.ADMIN_TYPES, default='content')
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # Create user
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_staff=True,
            is_superuser=False
        )
        user.set_password(validated_data['password'])
        user.save()
        
        # Create admin profile
        admin = Admin.objects.create(
            user=user,
            phone=validated_data.get('phone', ''),
            department=validated_data['department'],
            position=validated_data.get('position', ''),
            admin_type=validated_data['admin_type'],
            created_by=request.user.superadmin_profile if hasattr(request.user, 'superadmin_profile') else None
        )
        admin.set_permissions_from_type()
        
        return admin


# ==================== Independent Instructor Management ====================

class IndependentInstructorSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    verified_by_name = serializers.CharField(source='verified_by.user.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = IndependentInstructor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'total_courses', 'total_students', 'average_rating']


class IndependentInstructorCreateSerializer(serializers.Serializer):
    """Create a new independent instructor with user account"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    expertise = serializers.CharField(required=False, allow_blank=True)
    years_experience = serializers.IntegerField(default=0)
    commission_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, default=70)
    payment_email = serializers.EmailField(required=False, allow_blank=True)
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # Create user
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_staff=False,
            is_superuser=False
        )
        user.set_password(validated_data['password'])
        user.save()
        
        # Create instructor profile in accounts app
        from Account.models import Instructor
        instructor = Instructor.objects.create(
            user=user,
            phone_number=validated_data.get('phone', ''),
            bio=validated_data.get('bio', ''),
            Specialization=validated_data.get('expertise', '')
        )
        
        # Create independent instructor profile
        independent = IndependentInstructor.objects.create(
            user=user,
            bio=validated_data.get('bio', ''),
            expertise=validated_data.get('expertise', ''),
            years_experience=validated_data.get('years_experience', 0),
            commission_percentage=validated_data.get('commission_percentage', 70),
            payment_email=validated_data.get('payment_email', ''),
            created_by=request.user.superadmin_profile if hasattr(request.user, 'superadmin_profile') else None
        )
        
        return independent


class InstructorVerificationSerializer(serializers.Serializer):
    """Verify or reject an instructor"""
    action = serializers.ChoiceField(choices=['verify', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError("Rejection reason is required when rejecting")
        return data
    
    def save(self, instructor):
        request = self.context.get('request')
        
        if self.validated_data['action'] == 'verify':
            instructor.is_verified = True
            instructor.verified_by = request.user.superadmin_profile
            instructor.verified_at = timezone.now()
            instructor.rejection_reason = ''
        else:
            instructor.is_verified = False
            instructor.rejection_reason = self.validated_data['rejection_reason']
        
        instructor.save()
        return instructor


# ==================== Partner Management ====================

class PartnerSerializer(serializers.ModelSerializer):
    verified_by_name = serializers.CharField(source='verified_by.user.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)
    admin_users = UserBasicSerializer(many=True, read_only=True)
    
    class Meta:
        model = Partner
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'slug', 'total_instructors', 'total_courses', 'total_enrollments', 'total_revenue']


class PartnerCreateSerializer(serializers.ModelSerializer):
    admin_user_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    
    class Meta:
        model = Partner
        fields = [
            'name', 'partner_type', 'contact_email', 'contact_phone',
            'website', 'address', 'logo', 'banner', 'description',
            'commission_percentage', 'billing_email', 'tax_id',
            'max_instructors', 'max_courses', 'allow_own_branding',
            'admin_user_ids'
        ]
    
    def create(self, validated_data):
        admin_user_ids = validated_data.pop('admin_user_ids', [])
        request = self.context.get('request')
        
        # Create partner
        partner = Partner.objects.create(
            **validated_data,
            created_by=request.user.superadmin_profile if hasattr(request.user, 'superadmin_profile') else None
        )
        
        # Add admin users
        if admin_user_ids:
            users = User.objects.filter(id__in=admin_user_ids)
            partner.admin_users.add(*users)
        
        return partner


class PartnerAdminAddSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField())
    
    def save(self, partner):
        users = User.objects.filter(id__in=self.validated_data['user_ids'])
        partner.admin_users.add(*users)
        return partner


# ==================== Partner Instructor Management ====================

class PartnerInstructorSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    
    class Meta:
        model = PartnerInstructor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'total_courses', 'total_students']


class PartnerInstructorCreateSerializer(serializers.Serializer):
    """Create a new instructor for a partner"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    expertise = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField(required=False, allow_blank=True)
    is_primary = serializers.BooleanField(default=False)
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        partner_id = self.context.get('partner_id')
        partner = Partner.objects.get(id=partner_id)
        
        # Create user
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_staff=False,
            is_superuser=False
        )
        user.set_password(validated_data['password'])
        user.save()
        
        from Account.models import Instructor
        Instructor.objects.create(
            user=user,
            phone_number=validated_data.get('phone', ''),
            bio=validated_data.get('bio', ''),
            Specialization=validated_data.get('expertise', '')
        )
        
        # Create partner instructor profile
        partner_instructor = PartnerInstructor.objects.create(
            user=user,
            partner=partner,
            bio=validated_data.get('bio', ''),
            expertise=validated_data.get('expertise', ''),
            role=validated_data.get('role', ''),
            is_primary=validated_data.get('is_primary', False)
        )
        
        return partner_instructor


# ==================== System Settings ====================

class GlobalSettingSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = GlobalSetting
        fields = '__all__'
        read_only_fields = ['updated_at']
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)


class PlatformFeatureSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = PlatformFeature
        fields = '__all__'
        read_only_fields = ['updated_at']
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and hasattr(request.user, 'superadmin_profile'):
            validated_data['updated_by'] = request.user.superadmin_profile
        return super().update(instance, validated_data)


class SystemAnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = SystemAnnouncement
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and hasattr(request.user, 'superadmin_profile'):
            validated_data['created_by'] = request.user.superadmin_profile
        return super().create(validated_data)


# ==================== Notifications & Messages ====================

class NotificationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at', 'read_at']


class NotificationCreateSerializer(serializers.Serializer):
    """Create notification for one or multiple users"""
    user_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    target_role = serializers.ChoiceField(choices=['all', 'learner', 'instructor', 'partner', 'admin'], required=False)
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    notification_type = serializers.ChoiceField(choices=Notification.NOTIFICATION_TYPES, default='info')
    
    def validate(self, data):
        if not data.get('user_ids') and not data.get('target_role'):
            raise serializers.ValidationError("Either user_ids or target_role must be provided")
        return data
    
    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user_ids = validated_data.get('user_ids', [])
        target_role = validated_data.get('target_role')
        
        notifications = []
        
        if user_ids:
            users = User.objects.filter(id__in=user_ids)
            for user in users:
                notifications.append(Notification(
                    user=user,
                    title=validated_data['title'],
                    message=validated_data['message'],
                    notification_type=validated_data['notification_type']
                ))
        
        elif target_role:
            # Filter users by role
            if target_role == 'all':
                users = User.objects.filter(is_active=True)
            elif target_role == 'learner':
                users = User.objects.filter(learner_profile__isnull=False)
            elif target_role == 'instructor':
                users = User.objects.filter(instructor_profile__isnull=False)
            elif target_role == 'partner':
                users = User.objects.filter(partner_instructor_profile__isnull=False)
            elif target_role == 'admin':
                users = User.objects.filter(admin_profile__isnull=True)
            
            for user in users:
                notifications.append(Notification(
                    user=user,
                    title=validated_data['title'],
                    message=validated_data['message'],
                    notification_type=validated_data['notification_type']
                ))
        
        # Bulk create
        Notification.objects.bulk_create(notifications)
        
        return {
            'title': validated_data['title'],
            'count': len(notifications)
        }


class DirectMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    
    class Meta:
        model = DirectMessage
        fields = '__all__'
        read_only_fields = ['created_at', 'read_at']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


# ==================== Audit Log ====================

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['created_at']


# ==================== Reports ====================

class SystemReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = SystemReport
        fields = '__all__'
        read_only_fields = ['generated_at']


class ReportGenerateSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=SystemReport.REPORT_TYPES)
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    parameters = serializers.JSONField(default=dict, required=False)
    
    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data


# ==================== Dashboard Statistics ====================

class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    users = serializers.DictField()
    courses = serializers.DictField()
    partners = serializers.DictField()
    revenue = serializers.DictField()
    recent_activity = serializers.ListField()
    system_health = serializers.DictField()

# superadmin/serializers.py

class BackupRecordSerializer(serializers.ModelSerializer):
    """Serializer for BackupRecord model"""
    triggered_by_name = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = BackupRecord
        fields = [
            'id', 'name', 'backup_type', 'status',
            'file_path', 'file_size_mb', 'file_size_display',
            'includes_media', 'includes_database',
            'triggered_by', 'triggered_by_name',
            'started_at', 'completed_at', 'duration_seconds',
            'error_message'
        ]
        read_only_fields = ['started_at', 'completed_at']
    
    def get_triggered_by_name(self, obj):
        if obj.triggered_by and hasattr(obj.triggered_by, 'user'):
            return obj.triggered_by.user.get_full_name() or obj.triggered_by.user.username
        return None
    
    def get_duration_seconds(self, obj):
        if obj.completed_at and obj.started_at:
            duration = obj.completed_at - obj.started_at
            return int(duration.total_seconds())
        return None
    
    def get_file_size_display(self, obj):
        """Format file size for display"""
        if obj.file_size_mb:
            if obj.file_size_mb < 1:
                return f"{int(obj.file_size_mb * 1024)} KB"
            elif obj.file_size_mb < 1024:
                return f"{obj.file_size_mb:.2f} MB"
            else:
                return f"{obj.file_size_mb/1024:.2f} GB"
        return "N/A"


class BackupCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating backups"""
    class Meta:
        model = BackupRecord
        fields = [
            'name', 'backup_type', 
            'includes_media', 'includes_database'
        ]
    
    def validate(self, data):
        # Ensure at least one thing is backed up
        if not data.get('includes_media', True) and not data.get('includes_database', True):
            raise serializers.ValidationError(
                "At least one of includes_media or includes_database must be True"
            )
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # Auto-generate name if not provided
        if not validated_data.get('name'):
            from datetime import datetime
            backup_type = validated_data.get('backup_type', 'full')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            validated_data['name'] = f"{backup_type}_backup_{timestamp}"
        
        # Set triggered_by
        if request and hasattr(request.user, 'superadmin_profile'):
            validated_data['triggered_by'] = request.user.superadmin_profile
        
        return super().create(validated_data)


class BackupRecordSerializer(serializers.Serializer):
    """Serializer for updating backup status"""
    status = serializers.ChoiceField(choices=[
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ])
    file_path = serializers.CharField(required=False, allow_blank=True)
    file_size_mb = serializers.FloatField(required=False, min_value=0)
    error_message = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        
        if validated_data.get('file_path'):
            instance.file_path = validated_data['file_path']
        
        if validated_data.get('file_size_mb'):
            instance.file_size_mb = validated_data['file_size_mb']
        
        if validated_data.get('error_message'):
            instance.error_message = validated_data['error_message']
        
        # If status is completed or failed, set completed_at
        if instance.status in ['completed', 'failed'] and not instance.completed_at:
            from django.utils import timezone
            instance.completed_at = timezone.now()
        
        instance.save()
        return instance