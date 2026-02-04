from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.urls import reverse_lazy
from django.contrib import messages
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import TenantPartner
from .serilaizers import TenantPartnerSerializer
from accounts.models import Instructor, Learner
from courses.models import Course, Module, Lesson, Quizes

# ============= REST API ViewSets =============

class TenantPartnerViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing Tenant Partners
    Super admins can create, update, and approve partners
    """
    queryset = TenantPartner.objects.all()
    serializer_class = TenantPartnerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Super admins see all partners
        Partner admins see only their managed partners
        """
        user = self.request.user
        if user.is_superuser:
            return TenantPartner.objects.all()
        return TenantPartner.objects.filter(admin_user=user)
    
    def perform_create(self, serializer):
        """Set the creator when creating a new partner"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a partner (super admin only)"""
        if not request.user.is_superuser:
            return Response(
                {'error': 'Only super admins can approve partners'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        partner = self.get_object()
        partner.active = True
        partner.save()
        return Response({'status': 'Partner approved successfully'})
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for a partner"""
        partner = self.get_object()
        stats = {
            'total_students': partner.students.count(),
            'total_instructors': partner.instructors.count(),
            'total_courses': partner.courses.count(),
            'active_courses': partner.courses.filter(is_published=True).count(),
            'max_users': partner.max_users,
            'is_active': partner.is_active,
        }
        return Response(stats)


# ============= Partner Dashboard Views =============

def is_partner_admin(user):
    """Check if user is a partner admin"""
    return user.is_authenticated and (
        user.is_superuser or 
        user.managed_partners.exists()
    )

class PartnerDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Main dashboard for partner admins
    Shows overview of their organization
    """
    model = TenantPartner
    template_name = 'partern/dashboard/overview.html'
    context_object_name = 'partners'
    
    def test_func(self):
        return is_partner_admin(self.request.user)
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return TenantPartner.objects.all().annotate(
                student_count=Count('students'),
                instructor_count=Count('instructors'),
                course_count=Count('courses')
            )
        return user.managed_partners.all().annotate(
            student_count=Count('students'),
            instructor_count=Count('instructors'),
            course_count=Count('courses')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_superuser and self.request.user.managed_partners.exists():
            # Get the first partner for single partner admin
            partner = self.request.user.managed_partners.first()
            context['current_partner'] = partner
            context['students'] = partner.students.all()[:5]
            context['instructors'] = partner.instructors.all()[:5]
            context['courses'] = partner.courses.all()[:5]
        return context


class PartnerStudentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List all students for a partner
    Partner admin can manage their students
    """
    model = Learner
    template_name = 'partern/dashboard/student_list.html'
    context_object_name = 'students'
    paginate_by = 20
    
    def test_func(self):
        return is_partner_admin(self.request.user)
    
    def get_queryset(self):
        partner_id = self.kwargs.get('partner_id')
        partner = get_object_or_404(TenantPartner, id=partner_id)
        
        # Check permission
        if not self.request.user.is_superuser:
            if partner.admin_user != self.request.user:
                return Learner.objects.none()
        
        return partner.students.all().select_related('user').prefetch_related('enrolled_courses')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        partner_id = self.kwargs.get('partner_id')
        context['partner'] = get_object_or_404(TenantPartner, id=partner_id)
        return context


class PartnerInstructorListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List all instructors for a partner
    Partner admin can manage their instructors
    """
    model = Instructor
    template_name = 'partern/dashboard/instructor_list.html'
    context_object_name = 'instructors'
    paginate_by = 20
    
    def test_func(self):
        return is_partner_admin(self.request.user)
    
    def get_queryset(self):
        partner_id = self.kwargs.get('partner_id')
        partner = get_object_or_404(TenantPartner, id=partner_id)
        
        # Check permission
        if not self.request.user.is_superuser:
            if partner.admin_user != self.request.user:
                return Instructor.objects.none()
        
        return partner.instructors.all().select_related('user').annotate(
            course_count=Count('courses')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        partner_id = self.kwargs.get('partner_id')
        context['partner'] = get_object_or_404(TenantPartner, id=partner_id)
        return context


class PartnerCourseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List all courses for a partner
    Partner admin can manage their courses
    """
    model = Course
    template_name = 'partern/dashboard/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20
    
    def test_func(self):
        return is_partner_admin(self.request.user)
    
    def get_queryset(self):
        partner_id = self.kwargs.get('partner_id')
        partner = get_object_or_404(TenantPartner, id=partner_id)
        
        # Check permission
        if not self.request.user.is_superuser:
            if partner.admin_user != self.request.user:
                return Course.objects.none()
        
        return partner.courses.all().select_related('instructor__user').annotate(
            student_count=Count('learners')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        partner_id = self.kwargs.get('partner_id')
        context['partner'] = get_object_or_404(TenantPartner, id=partner_id)
        return context


# ============= Super Admin Views =============

class SuperAdminPartnerListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Super admin view to see and manage all partners
    """
    model = TenantPartner
    template_name = 'partern/superadmin/partner_list.html'
    context_object_name = 'partners'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_queryset(self):
        return TenantPartner.objects.all().select_related('admin_user', 'created_by').annotate(
            student_count=Count('students'),
            instructor_count=Count('instructors'),
            course_count=Count('courses')
        ).order_by('-created_at')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_partner(request, partner_id):
    """
    Super admin approves a partner
    """
    partner = get_object_or_404(TenantPartner, id=partner_id)
    partner.active = True
    partner.save()
    messages.success(request, f"Partner '{partner.name}' has been approved successfully!")
    return redirect('superadmin_partner_list')

class PublicPartnerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API for listing active partners
    """
    serializer_class = TenantPartnerSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        from django.utils import timezone
        # Filter for active partners that haven't expired
        return TenantPartner.objects.filter(
            active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=timezone.now().date())
        )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def deactivate_partner(request, partner_id):
    """
    Super admin deactivates a partner
    """
    partner = get_object_or_404(TenantPartner, id=partner_id)
    partner.active = False
    partner.save()
    messages.warning(request, f"Partner '{partner.name}' has been deactivated.")
    return redirect('superadmin_partner_list')