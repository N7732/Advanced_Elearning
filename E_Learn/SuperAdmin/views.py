# superadmin/views.py
from rest_framework import generics, permissions, status, views, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.hashers import make_password
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
from .models import *
from .serializers import *
from .permission import IsSuperAdmin
from Courses.models import Course, Enrollment
import logging
from django_filters.rest_framework import DjangoFilterBackend

logger = logging.getLogger(__name__)
User = get_user_model()


# ==================== SuperAdmin Authentication ====================

class SuperAdminLoginView(views.APIView):
    """
    Login view for superadmin - redirects to superadmin dashboard
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Check if user is superadmin (either Django superuser or has superadmin profile)
            if user.is_superuser or hasattr(user, 'superadmin_profile'):
                # Login the user
                login(request, user)
                
                # Update last login IP
                if hasattr(user, 'superadmin_profile'):
                    ip = request.META.get('REMOTE_ADDR')
                    user.superadmin_profile.last_login_ip = ip
                    user.superadmin_profile.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=user,
                    action='login',
                    action_description='Superadmin logged in',
                    target_model='User',
                    target_id=user.id,
                    target_repr=str(user),
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Return success with redirect info
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': '/superadmin/dashboard',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_superuser': user.is_superuser,
                        'has_superadmin_profile': hasattr(user, 'superadmin_profile')
                    }
                })
            else:
                return Response(
                    {'error': 'Access denied. Superadmin privileges required.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )


# ==================== SuperAdmin Profile Management ====================

class SuperAdminProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current superadmin profile
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = SuperAdminSerializer
    
    def get_object(self):
        if not hasattr(self.request.user, 'superadmin_profile'):
            # Create profile if doesn't exist
            return SuperAdmin.objects.create(user=self.request.user)
        return self.request.user.superadmin_profile


class SuperAdminCreateView(generics.CreateAPIView):
    """
    Create a new superadmin (only existing superadmins can do this)
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = SuperAdminCreateSerializer


# ==================== Admin Management ====================

class AdminListView(generics.ListCreateAPIView):
    """
    List all admins or create a new admin
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['admin_type', 'is_active', 'department']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'last_login', 'user__username']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminCreateSerializer
        return AdminSerializer
    
    def get_queryset(self):
        return Admin.objects.select_related('user', 'created_by__user').all()


class AdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an admin
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AdminSerializer
        return AdminSerializer
    
    def get_queryset(self):
        return Admin.objects.select_related('user', 'created_by__user')
    
    def perform_destroy(self, instance):
        # Deactivate user instead of deleting
        instance.user.is_active = False
        instance.user.save()
        instance.is_active = False
        instance.save()


class AdminActivateView(views.APIView):
    """
    Activate or deactivate an admin
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def post(self, request, pk):
        admin = get_object_or_404(Admin, pk=pk)
        action = request.data.get('action')
        
        if action == 'activate':
            admin.is_active = True
            admin.user.is_active = True
        elif action == 'deactivate':
            admin.is_active = False
            admin.user.is_active = False
        else:
            return Response(
                {'error': 'Invalid action. Use "activate" or "deactivate"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        admin.user.save()
        admin.save()
        
        return Response({'status': 'success', 'is_active': admin.is_active})


# ==================== Independent Instructor Management ====================

class IndependentInstructorListView(generics.ListCreateAPIView):
    """
    List all independent instructors or create a new one
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_verified', 'is_active']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'expertise']
    ordering_fields = ['created_at', 'years_experience', 'total_courses']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IndependentInstructorCreateSerializer
        return IndependentInstructorSerializer
    
    def get_queryset(self):
        return IndependentInstructor.objects.select_related(
            'user', 'verified_by__user', 'created_by__user'
        ).all()


class IndependentInstructorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an independent instructor
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def get_serializer_class(self):
        return IndependentInstructorSerializer
    
    def get_queryset(self):
        return IndependentInstructor.objects.select_related(
            'user', 'verified_by__user', 'created_by__user'
        )
    
    def perform_destroy(self, instance):
        # Deactivate instead of delete
        instance.user.is_active = False
        instance.user.save()
        instance.is_active = False
        instance.save()


class InstructorVerificationView(views.APIView):
    """
    Verify or reject an instructor
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def post(self, request, pk):
        instructor = get_object_or_404(IndependentInstructor, pk=pk)
        serializer = InstructorVerificationSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            instructor = serializer.save(instructor)
            return Response(IndependentInstructorSerializer(instructor).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== Partner Management ====================

class PartnerListView(generics.ListCreateAPIView):
    """
    List all partners or create a new partner
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['partner_type', 'is_active', 'verified']
    search_fields = ['name', 'contact_email', 'description']
    ordering_fields = ['created_at', 'name', 'total_courses']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PartnerCreateSerializer
        return PartnerSerializer
    
    def get_queryset(self):
        return Partner.objects.select_related('verified_by__user', 'created_by__user').prefetch_related('admin_users')


class PartnerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a partner
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PartnerCreateSerializer
        return PartnerSerializer
    
    def get_queryset(self):
        return Partner.objects.select_related('verified_by__user', 'created_by__user').prefetch_related('admin_users')
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class PartnerVerifyView(views.APIView):
    """
    Verify a partner
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def post(self, request, pk):
        partner = get_object_or_404(Partner, pk=pk)
        partner.verified = True
        partner.verified_by = request.user.superadmin_profile
        partner.save()
        
        return Response(PartnerSerializer(partner).data)


class PartnerAdminAddView(views.APIView):
    """
    Add admin users to a partner
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def post(self, request, pk):
        partner = get_object_or_404(Partner, pk=pk)
        serializer = PartnerAdminAddSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(partner)
            return Response(PartnerSerializer(partner).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PartnerInstructorListView(generics.ListCreateAPIView):
    """
    List all instructors for a partner or create a new one
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PartnerInstructorCreateSerializer
        return PartnerInstructorSerializer
    
    def get_queryset(self):
        partner_id = self.kwargs.get('partner_id')
        return PartnerInstructor.objects.filter(partner_id=partner_id).select_related('user', 'partner')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['partner_id'] = self.kwargs.get('partner_id')
        return context


# ==================== System Settings ====================

class GlobalSettingView(generics.RetrieveUpdateAPIView):
    """
    Get or update global settings
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = GlobalSettingSerializer
    
    def get_object(self):
        obj, created = GlobalSetting.objects.get_or_create(pk=1)
        return obj


class PlatformFeatureListView(generics.ListCreateAPIView):
    """
    List all platform features or create a new one
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = PlatformFeatureSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']
    
    def get_queryset(self):
        return PlatformFeature.objects.all()


class PlatformFeatureDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a platform feature
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = PlatformFeatureSerializer
    queryset = PlatformFeature.objects.all()


class SystemAnnouncementListView(generics.ListCreateAPIView):
    """
    List all system announcements or create a new one
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = SystemAnnouncementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['priority']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'start_date', 'priority']
    
    def get_queryset(self):
        return SystemAnnouncement.objects.select_related('created_by__user').all()


class SystemAnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a system announcement
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = SystemAnnouncementSerializer
    queryset = SystemAnnouncement.objects.all()


# ==================== Notifications & Messages ====================

class NotificationListView(generics.ListAPIView):
    """
    List all notifications
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'is_read']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        return Notification.objects.select_related('user').all()


class NotificationCreateView(generics.CreateAPIView):
    """
    Create notifications for users
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = NotificationCreateSerializer


class DirectMessageListView(generics.ListCreateAPIView):
    """
    List all direct messages or send a new one
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = DirectMessageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_read']
    search_fields = ['subject', 'body']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        return DirectMessage.objects.select_related('sender', 'recipient').all()
    
    def perform_create(self, serializer):
        serializer.save()


class DirectMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a direct message
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = DirectMessageSerializer
    queryset = DirectMessage.objects.all()


# ==================== Audit Logs ====================

class AuditLogListView(generics.ListAPIView):
    """
    List all audit logs
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'target_model']
    search_fields = ['action_description', 'target_repr', 'username']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        return AuditLog.objects.select_related('user').all()


class AuditLogDetailView(generics.RetrieveAPIView):
    """
    Retrieve an audit log entry
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()


# ==================== Reports ====================

class SystemReportListView(generics.ListCreateAPIView):
    """
    List all reports or generate a new report
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReportGenerateSerializer
        return SystemReportSerializer
    
    def get_queryset(self):
        return SystemReport.objects.select_related('generated_by__user').all()
    
    def perform_create(self, serializer):
        # Generate report based on parameters
        validated_data = serializer.validated_data
        request = self.request
        
        # Here you would implement actual report generation logic
        # For now, we'll create a placeholder
        report = SystemReport.objects.create(
            title=f"{validated_data['report_type']} Report",
            report_type=validated_data['report_type'],
            data={'message': 'Report generation logic to be implemented'},
            parameters=validated_data.get('parameters', {}),
            generated_by=request.user.superadmin_profile if hasattr(request.user, 'superadmin_profile') else None,
            start_date=validated_data['start_date'],
            end_date=validated_data['end_date']
        )
        
        return report


class SystemReportDetailView(generics.RetrieveDestroyAPIView):
    """
    Retrieve or delete a report
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = SystemReportSerializer
    queryset = SystemReport.objects.all()


# ==================== Dashboard ====================

class SuperAdminDashboardView(views.APIView):
    """
    Get dashboard statistics for superadmin
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def get(self, request):
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        learners = User.objects.filter(learner_profile__isnull=False).count()
        instructors = User.objects.filter(instructor_profile__isnull=False).count()
        admins = Admin.objects.count()
        superadmins = SuperAdmin.objects.count()
        
        # Course statistics
        from Courses.models import Course, Lesson, Module
        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(is_published=True).count()
        total_lessons = Lesson.objects.count()
        total_modules = Module.objects.count()
        
        # Enrollment statistics
        total_enrollments = Enrollment.objects.count()
        active_enrollments = Enrollment.objects.filter(status='active').count()
        completed_enrollments = Enrollment.objects.filter(status='completed').count()
        
        # Partner statistics
        total_partners = Partner.objects.count()
        active_partners = Partner.objects.filter(is_active=True).count()
        verified_partners = Partner.objects.filter(verified=True).count()
        
        # Revenue (placeholder - implement actual payment logic)
        total_revenue = 0
        
        # Recent activity
        recent_logs = AuditLog.objects.select_related('user').order_by('-created_at')[:10]
        recent_activity = AuditLogSerializer(recent_logs, many=True).data
        
        # System health
        system_health = {
            'status': 'healthy',
            'last_backup': BackupRecord.objects.filter(status='completed').order_by('-completed_at').first().completed_at if BackupRecord.objects.exists() else None,
            'pending_backups': BackupRecord.objects.filter(status='pending').count(),
        }
        
        # Chart data (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        daily_users = User.objects.filter(date_joined__gte=thirty_days_ago).extra(
            {'date': "date(date_joined)"}
        ).values('date').annotate(count=Count('id')).order_by('date')
        
        daily_enrollments = Enrollment.objects.filter(enrolled_at__gte=thirty_days_ago).extra(
            {'date': "date(enrolled_at)"}
        ).values('date').annotate(count=Count('id')).order_by('date')
        
        return Response({
            'users': {
                'total': total_users,
                'active': active_users,
                'learners': learners,
                'instructors': instructors,
                'admins': admins,
                'superadmins': superadmins,
                'daily_new': daily_users,
            },
            'courses': {
                'total': total_courses,
                'published': published_courses,
                'lessons': total_lessons,
                'modules': total_modules,
            },
            'enrollments': {
                'total': total_enrollments,
                'active': active_enrollments,
                'completed': completed_enrollments,
                'daily': daily_enrollments,
            },
            'partners': {
                'total': total_partners,
                'active': active_partners,
                'verified': verified_partners,
            },
            'revenue': {
                'total': total_revenue,
                'this_month': 0,
            },
            'recent_activity': recent_activity,
            'system_health': system_health,
        })


class SystemHealthView(views.APIView):
    """
    Get detailed system health information
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    def get(self, request):
        # Check database connection
        from django.db import connection
        db_status = 'connected'
        try:
            connection.ensure_connection()
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        # Check storage
        import os
        from django.conf import settings
        
        media_path = settings.MEDIA_ROOT
        media_usage = 0
        if os.path.exists(media_path):
            for root, dirs, files in os.walk(media_path):
                media_usage += sum(os.path.getsize(os.path.join(root, name)) for name in files)
        
        # Convert to MB
        media_usage_mb = media_usage / (1024 * 1024)
        
        # Queue status (if using celery)
        queue_status = 'not_configured'
        
        # Last backup
        last_backup = BackupRecord.objects.filter(status='completed').order_by('-completed_at').first()
        
        return Response({
            'database': {
                'status': db_status,
                'backend': connection.vendor,
            },
            'storage': {
                'media_usage_mb': round(media_usage_mb, 2),
                'media_path': str(media_path),
            },
            'queue': {
                'status': queue_status,
            },
            'backups': {
                'last_backup': BackupRecordSerializer(last_backup).data if last_backup else None,
                'total_backups': BackupRecord.objects.count(),
                'failed_backups': BackupRecord.objects.filter(status='failed').count(),
            },
            'cache': {
                'status': 'healthy',  # Placeholder
            },
            'server_time': timezone.now(),
        })


# ==================== Backup Management ====================


class BackupListView(generics.ListCreateAPIView):
    """
    List all backups or create a new backup
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = BackupRecordSerializer
    
    def get_queryset(self):
        return BackupRecord.objects.all()
    
    def perform_create(self, serializer):
        request = self.request
        backup = serializer.save(
            triggered_by=request.user.superadmin_profile if hasattr(request.user, 'superadmin_profile') else None,
            status='pending'
        )
        
        # Trigger backup task here (Celery task)
        # trigger_backup.delay(backup.id)
        
        return backup


class BackupDetailView(generics.RetrieveDestroyAPIView):
    """
    Retrieve or delete a backup
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = BackupRecordSerializer
    queryset = BackupRecord.objects.all()