# partner/views.py
from rest_framework import generics, permissions, status, filters, views
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Q, Count, Sum, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .serializers import *
from .permissions import IsSuperAdminOrPartnerAdmin, IsPartnerAdmin, CanManagePartner
import logging

logger = logging.getLogger(__name__)

# ==================== PARTNER MAIN VIEWS ====================

class PartnerListView(generics.ListCreateAPIView):
    """
    List all partners or create a new partner
    - GET: Returns list of partners (filtered by user role)
    - POST: Create new partner (superadmin only)
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'partner_type': ['exact'],
        'partnership_tier': ['exact'],
        'verification_status': ['exact'],
        'is_active': ['exact'],
        'is_featured': ['exact'],
        'country': ['exact', 'icontains'],
        'created_at': ['gte', 'lte', 'date'],
    }
    
    search_fields = ['name', 'contact_email', 'short_description', 'city']
    ordering_fields = ['name', 'created_at', 'total_students', 'total_courses', 'average_rating']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PartnerCreateUpdateSerializer
        return PartnerListSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Base queryset with optimizations
        queryset = Partner.objects.select_related(
            'primary_admin', 'created_by', 'verified_by'
        ).prefetch_related(
            'campuses', 'partner_admin_relations__user'
        )
        
        # Filter based on user role
        if user.is_superuser or hasattr(user, 'superadmin_profile'):
            # Superadmins see all
            return queryset
        
        elif hasattr(user, 'partner_admin_relations'):
            # Partner admins see only their partners
            partner_ids = user.partner_admin_relations.values_list('partner_id', flat=True)
            return queryset.filter(id__in=partner_ids)
        
        elif hasattr(user, 'partner_instructor_profiles'):
            # Partner instructors see their partner
            partner_ids = user.partner_instructor_profiles.values_list('partner_id', flat=True)
            return queryset.filter(id__in=partner_ids)
        
        else:
            # Regular users see only active public partners
            return queryset.filter(is_active=True, is_public=True)
    
    def perform_create(self, serializer):
        # Only superadmin can create partners
        if not (self.request.user.is_superuser or hasattr(self.request.user, 'superadmin_profile')):
            raise PermissionDenied("Only superadmins can create partners")
        
        serializer.save()


class PartnerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a partner
    - GET: Get partner details
    - PUT/PATCH: Update partner (superadmin only)
    - DELETE: Deactivate partner (superadmin only)
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PartnerCreateUpdateSerializer
        return PartnerDetailSerializer
    
    def get_queryset(self):
        return Partner.objects.select_related(
            'primary_admin', 'created_by', 'verified_by'
        ).prefetch_related(
            'campuses__faculties__departments',
            'campuses__departments',
            'partner_admin_relations__user',
            'instructors__user',
            'documents',
            'activity_logs__user'
        )
    
    def perform_destroy(self, instance):
        # Soft delete - just deactivate
        instance.is_active = False
        instance.save()
        
        # Log activity
        PartnerActivityLog.objects.create(
            partner=instance,
            user=self.request.user,
            action='DEACTIVATE',
            details={'method': 'api_delete'},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )


class PartnerVerificationView(views.APIView):
    """
    Verify, reject, or suspend a partner
    POST /api/partners/{slug}/verify/
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrPartnerAdmin]
    
    def post(self, request, slug):
        partner = get_object_or_404(Partner, slug=slug)
        
        serializer = PartnerVerificationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            partner = serializer.save(partner)
            return Response(
                PartnerDetailSerializer(partner, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PartnerDashboardView(views.APIView):
    """
    Get dashboard statistics for a partner
    GET /api/partners/{slug}/dashboard/
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    
    def get(self, request, slug):
        partner = get_object_or_404(Partner, slug=slug)
        
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        since_date = timezone.now() - timezone.timedelta(days=days)
        
        # Calculate statistics
        from Courses.models import Course, Enrollment
        
        # Overview stats
        total_courses = Course.objects.filter(partner=partner).count()
        active_courses = Course.objects.filter(partner=partner, is_published=True).count()
        
        total_enrollments = Enrollment.objects.filter(course__partner=partner).count()
        active_enrollments = Enrollment.objects.filter(
            course__partner=partner,
            status='active'
        ).count()
        completed_enrollments = Enrollment.objects.filter(
            course__partner=partner,
            status='completed'
        ).count()
        
        # Revenue (placeholder - implement actual payment logic)
        total_revenue = 0
        
        # Recent enrollments
        recent_enrollments = Enrollment.objects.filter(
            course__partner=partner
        ).select_related('learner__user', 'course').order_by('-enrolled_at')[:10]
        
        # Top courses
        top_courses = Course.objects.filter(partner=partner).annotate(
            student_count=Count('enrollments')
        ).order_by('-student_count')[:5]
        
        # Trends (last 30 days vs previous 30)
        previous_date = since_date - timezone.timedelta(days=days)
        
        current_period_enrollments = Enrollment.objects.filter(
            course__partner=partner,
            enrolled_at__gte=since_date
        ).count()
        
        previous_period_enrollments = Enrollment.objects.filter(
            course__partner=partner,
            enrolled_at__gte=previous_date,
            enrolled_at__lt=since_date
        ).count()
        
        enrollment_growth = 0
        if previous_period_enrollments > 0:
            enrollment_growth = ((current_period_enrollments - previous_period_enrollments) / previous_period_enrollments) * 100
        
        return Response({
            'overview': {
                'total_courses': total_courses,
                'active_courses': active_courses,
                'total_enrollments': total_enrollments,
                'active_enrollments': active_enrollments,
                'completed_enrollments': completed_enrollments,
                'completion_rate': round((completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0, 1),
                'total_revenue': total_revenue,
            },
            'trends': {
                'enrollments': {
                    'current_period': current_period_enrollments,
                    'previous_period': previous_period_enrollments,
                    'growth': round(enrollment_growth, 1)
                }
            },
            'top_courses': [
                {
                    'id': course.id,
                    'title': course.title,
                    'students': course.student_count,
                    'rating': float(course.average_rating)
                }
                for course in top_courses
            ],
            'recent_enrollments': [
                {
                    'id': e.id,
                    'student_name': e.learner.user.get_full_name(),
                    'course_title': e.course.title,
                    'enrolled_at': e.enrolled_at,
                    'status': e.status
                }
                for e in recent_enrollments
            ],
            'usage': {
                'students': {
                    'used': partner.total_students,
                    'limit': partner.max_students,
                    'percentage': round((partner.total_students / partner.max_students * 100) if partner.max_students > 0 else 0, 1)
                },
                'courses': {
                    'used': partner.total_courses,
                    'limit': partner.max_courses,
                    'percentage': round((partner.total_courses / partner.max_courses * 100) if partner.max_courses > 0 else 0, 1)
                },
                'instructors': {
                    'used': partner.total_instructors,
                    'limit': partner.max_instructors,
                    'percentage': round((partner.total_instructors / partner.max_instructors * 100) if partner.max_instructors > 0 else 0, 1)
                }
            }
        })


# ==================== ADMIN MANAGEMENT VIEWS ====================

class PartnerAdminListView(generics.ListCreateAPIView):
    """
    List and add admins for a partner
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = PartnerAdminSerializer
    
    def get_queryset(self):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        return PartnerAdmin.objects.filter(partner=partner).select_related('user', 'partner')
    
    def perform_create(self, serializer):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        
        # Check quota
        if partner.admins.count() >= partner.max_admins:
            raise ValidationError(f"Maximum number of admins ({partner.max_admins}) reached")
        
        serializer.save(partner=partner)


class PartnerAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a partner admin
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = PartnerAdminSerializer
    
    def get_queryset(self):
        return PartnerAdmin.objects.select_related('user', 'partner')


# ==================== INSTRUCTOR MANAGEMENT VIEWS ====================

class PartnerInstructorListView(generics.ListCreateAPIView):
    """
    List and add instructors for a partner
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = PartnerInstructorSerializer
    
    def get_queryset(self):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        return PartnerInstructor.objects.filter(partner=partner).select_related('user', 'partner')
    
    def perform_create(self, serializer):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        
        # Check quota
        if partner.instructors.count() >= partner.max_instructors:
            raise ValidationError(f"Maximum number of instructors ({partner.max_instructors}) reached")
        
        serializer.save(partner=partner)


class PartnerInstructorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a partner instructor
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = PartnerInstructorSerializer
    
    def get_queryset(self):
        return PartnerInstructor.objects.select_related('user', 'partner')


# ==================== CAMPUS MANAGEMENT VIEWS ====================

class CampusListView(generics.ListCreateAPIView):
    """
    List and create campuses for a partner
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = CampusSerializer
    
    def get_queryset(self):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        return Campus.objects.filter(partner=partner).prefetch_related('faculties', 'departments')
    
    def perform_create(self, serializer):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        serializer.save(partner=partner)


class CampusDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a campus
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = CampusSerializer
    queryset = Campus.objects.all()


# ==================== FACULTY MANAGEMENT VIEWS ====================

class FacultyListView(generics.ListCreateAPIView):
    """
    List and create faculties for a campus
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = FacultySerializer
    
    def get_queryset(self):
        campus = get_object_or_404(Campus, id=self.kwargs['campus_id'])
        return Faculty.objects.filter(campus=campus).prefetch_related('departments')
    
    def perform_create(self, serializer):
        campus = get_object_or_404(Campus, id=self.kwargs['campus_id'])
        serializer.save(campus=campus)


class FacultyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a faculty
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = FacultySerializer
    queryset = Faculty.objects.all()


# ==================== DEPARTMENT MANAGEMENT VIEWS ====================

class DepartmentListView(generics.ListCreateAPIView):
    """
    List and create departments
    Can be under a faculty or directly under campus
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = DepartmentSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']
    
    def get_queryset(self):
        # Can filter by faculty or campus
        faculty_id = self.request.query_params.get('faculty')
        campus_id = self.request.query_params.get('campus')
        
        if faculty_id:
            return Department.objects.filter(faculty_id=faculty_id).select_related('faculty', 'campus')
        elif campus_id:
            return Department.objects.filter(campus_id=campus_id).select_related('faculty', 'campus')
        else:
            return Department.objects.none()
    
    def perform_create(self, serializer):
        # Must provide either faculty or campus
        faculty_id = self.request.data.get('faculty')
        campus_id = self.request.data.get('campus')
        
        if faculty_id:
            faculty = get_object_or_404(Faculty, id=faculty_id)
            serializer.save(faculty=faculty)
        elif campus_id:
            campus = get_object_or_404(Campus, id=campus_id)
            serializer.save(campus=campus)
        else:
            raise ValidationError("Must specify either faculty or campus")


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a department
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = DepartmentSerializer
    queryset = Department.objects.all()


# ==================== DOCUMENT MANAGEMENT VIEWS ====================

class PartnerDocumentListView(generics.ListCreateAPIView):
    """
    List and upload documents for a partner
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = PartnerDocumentSerializer
    
    def get_queryset(self):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        return PartnerDocument.objects.filter(partner=partner).order_by('-uploaded_at')
    
    def perform_create(self, serializer):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        serializer.save(
            partner=partner,
            uploaded_by=self.request.user
        )


class PartnerDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a document
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = PartnerDocumentSerializer
    
    def get_queryset(self):
        return PartnerDocument.objects.all()
    
    def perform_destroy(self, instance):
        # Delete the file from storage
        if instance.file:
            instance.file.delete()
        instance.delete()


class PartnerDocumentVerifyView(views.APIView):
    """
    Verify a document
    POST /api/partners/{slug}/documents/{id}/verify/
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrPartnerAdmin]
    
    def post(self, request, slug, pk):
        document = get_object_or_404(PartnerDocument, pk=pk, partner__slug=slug)
        
        document.is_verified = True
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        return Response(
            PartnerDocumentSerializer(document, context={'request': request}).data
        )


# ==================== INVITATION MANAGEMENT VIEWS ====================

class PartnerInvitationListView(generics.ListCreateAPIView):
    """
    List and create invitations for a partner
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PartnerInvitationCreateSerializer
        return PartnerInvitationSerializer
    
    def get_queryset(self):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        return PartnerInvitation.objects.filter(partner=partner).order_by('-created_at')
    
    def perform_create(self, serializer):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        serializer.context['partner'] = partner
        serializer.save()


class PartnerInvitationDetailView(generics.RetrieveDestroyAPIView):
    """
    Retrieve or cancel an invitation
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = PartnerInvitationSerializer
    
    def get_queryset(self):
        return PartnerInvitation.objects.all()
    
    def perform_destroy(self, instance):
        instance.status = 'cancelled'
        instance.save()


class AcceptInvitationView(views.APIView):
    """
    Public endpoint to accept an invitation
    GET /api/partner/invitations/accept/{token}/
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        invitation = get_object_or_404(PartnerInvitation, token=token, status='pending')
        
        if invitation.is_expired:
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {'error': 'Invitation has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'partner': invitation.partner.name,
            'email': invitation.email,
            'role': invitation.role,
            'expires_at': invitation.expires_at
        })
    
    def post(self, request, token):
        invitation = get_object_or_404(PartnerInvitation, token=token, status='pending')
        
        if invitation.is_expired:
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {'error': 'Invitation has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists
        email = invitation.email
        user = User.objects.filter(email=email).first()
        
        if not user:
            # User needs to register first
            return Response({
                'requires_registration': True,
                'email': email,
                'partner': invitation.partner.name,
                'token': str(token)
            })
        
        # Accept invitation
        success, message = invitation.accept(user)
        
        if success:
            return Response({'success': True, 'message': message})
        else:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


# ==================== ACTIVITY LOG VIEWS ====================

class PartnerActivityLogListView(generics.ListAPIView):
    """
    List activity logs for a partner
    """
    permission_classes = [permissions.IsAuthenticated, CanManagePartner]
    serializer_class = PartnerActivityLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'user']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        return PartnerActivityLog.objects.filter(partner=partner).select_related('user')


# ==================== SUBSCRIPTION VIEWS ====================

class PartnerSubscriptionListView(generics.ListCreateAPIView):
    """
    List and create subscriptions for a partner
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrPartnerAdmin]
    serializer_class = PartnerSubscriptionSerializer
    
    def get_queryset(self):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        return PartnerSubscription.objects.filter(partner=partner).order_by('-start_date')
    
    def perform_create(self, serializer):
        partner = get_object_or_404(Partner, slug=self.kwargs['slug'])
        serializer.save(partner=partner)


class PartnerSubscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a subscription
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrPartnerAdmin]
    serializer_class = PartnerSubscriptionSerializer
    queryset = PartnerSubscription.objects.all()


# ==================== PUBLIC PARTNER VIEWS ====================

class PublicPartnerListView(generics.ListAPIView):
    """
    Public endpoint to list active partners
    No authentication required
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PartnerListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'partner_type': ['exact'],
        'country': ['exact'],
        'is_featured': ['exact'],
    }
    
    search_fields = ['name', 'short_description', 'city']
    ordering_fields = ['name', 'average_rating', 'total_courses']
    ordering = ['-is_featured', 'name']
    
    def get_queryset(self):
        return Partner.objects.filter(
            is_active=True,
            is_public=True,
            verification_status='verified'
        ).select_related('primary_admin')


class PublicPartnerDetailView(generics.RetrieveAPIView):
    """
    Public endpoint to view partner details
    No authentication required
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PartnerDetailSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Partner.objects.filter(
            is_active=True,
            is_public=True,
            verification_status='verified'
        )