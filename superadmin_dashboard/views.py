from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from partern.models import TenantPartner
from accounts.models import User, Learner, Instructor
from courses.models import Course
from .models import GlobalSetting, Notification, DirectMessage, AuditLog
from .forms import TenantPartnerForm, DirectMessageForm
from .utils import log_action
from django.db import models
from django.core.paginator import Paginator

class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

class OverviewView(LoginRequiredMixin, SuperAdminRequiredMixin, TemplateView):
    template_name = 'superadmin_dashboard/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_partners'] = TenantPartner.objects.count()
        context['total_users'] = User.objects.count()
        context['total_learners'] = Learner.objects.count()
        context['total_instructors'] = Instructor.objects.count()
        context['total_courses'] = Course.objects.count()
        context['recent_partners'] = TenantPartner.objects.order_by('-created_at')[:5]
        context['recent_courses'] = Course.objects.order_by('-created_at')[:5]
        context['pending_requests'] = TenantPartner.objects.filter(is_approved_by_RDB=False).count()
        return context

class TenantListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = TenantPartner
    template_name = 'superadmin_dashboard/tenant_list.html'
    context_object_name = 'tenants'
    paginate_by = 10
    ordering = ['-created_at']

def toggle_tenant_status(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Permission denied.")
        return redirect('superadmin_dashboard:overview')
    
    tenant = get_object_or_404(TenantPartner, pk=pk)
    tenant.active = not tenant.active
    tenant.save()
    status = "activated" if tenant.active else "suspended"
    log_action(request.user, f"Toggled tenant status: {status}", "TenantPartner", tenant.id, request=request)
    messages.success(request, f"Tenant {tenant.name} has been {status}.")
    return redirect('superadmin_dashboard:tenant_list')

def toggle_rdb_approval(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Permission denied.")
        return redirect('superadmin_dashboard:overview')
    
    tenant = get_object_or_404(TenantPartner, pk=pk)
    tenant.is_approved_by_RDB = not tenant.is_approved_by_RDB
    tenant.save()
    log_action(request.user, "Toggled RDB approval", "TenantPartner", tenant.id, request=request)
    return redirect('superadmin_dashboard:tenant_list')

class TenantCreateView(LoginRequiredMixin, SuperAdminRequiredMixin, CreateView):
    model = TenantPartner
    form_class = TenantPartnerForm
    template_name = 'superadmin_dashboard/tenant_form.html'
    success_url = reverse_lazy('superadmin_dashboard:tenant_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        log_action(self.request.user, "Created new tenant", "TenantPartner", self.object.id, request=self.request)
        messages.success(self.request, "Tenant created successfully.")
        return response

class TenantUpdateView(LoginRequiredMixin, SuperAdminRequiredMixin, UpdateView):
    model = TenantPartner
    form_class = TenantPartnerForm
    template_name = 'superadmin_dashboard/tenant_form.html'
    success_url = reverse_lazy('superadmin_dashboard:tenant_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(self.request.user, "Updated tenant", "TenantPartner", self.object.id, request=self.request)
        messages.success(self.request, "Tenant updated successfully.")
        return response

class LearnerListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = Learner
    template_name = 'superadmin_dashboard/learner_list.html'
    context_object_name = 'learners'
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(user__is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(user__is_active=False)
        
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(user__username__icontains=search_query) | queryset.filter(user__email__icontains=search_query)
        return queryset

class InstructorListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = Instructor
    template_name = 'superadmin_dashboard/instructor_list.html'
    context_object_name = 'instructors'
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(user__is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(user__is_active=False)
            
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(user__username__icontains=search_query) | queryset.filter(user__email__icontains=search_query)
        return queryset

class GlobalCourseListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = Course
    template_name = 'superadmin_dashboard/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        partner_id = self.request.GET.get('partner')
        if partner_id:
            queryset = queryset.filter(partner_id=partner_id)
        
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(title__icontains=search_query) | queryset.filter(instructor__user__username__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partners'] = TenantPartner.objects.all()
        return context

class AdminUserListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    # For managing Tenant Admins and other staff
    model = User
    template_name = 'superadmin_dashboard/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        # Exclude learners and instructors as they have their own lists
        return User.objects.exclude(user_type__in=['learner', 'instructor']).order_by('-date_joined')

def toggle_instructor_approval(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Permission denied.")
        return redirect('superadmin_dashboard:overview')
    
    instructor = get_object_or_404(Instructor, pk=pk)
    instructor.is_approved = not instructor.is_approved
    instructor.save()
    status = "approved" if instructor.is_approved else "unapproved"
    log_action(request.user, f"Toggled instructor approval: {status}", "Instructor", instructor.id, request=request)
    messages.success(request, f"Instructor {instructor.user.get_full_name()} has been {status}.")
    return redirect('superadmin_dashboard:instructor_list')

class GlobalSettingsView(LoginRequiredMixin, SuperAdminRequiredMixin, UpdateView):
    model = GlobalSetting
    fields = ['site_name', 'contact_email', 'phone_number', 'address', 'site_logo', 'favicon', 'maintenance_mode']
    template_name = 'superadmin_dashboard/settings_form.html'
    success_url = reverse_lazy('superadmin_dashboard:overview')

    def get_object(self, queryset=None):
        obj, created = GlobalSetting.objects.get_or_create(id=1)
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(self.request.user, "Updated global settings", "GlobalSetting", self.object.id, request=self.request)
        messages.success(self.request, "Global settings updated successfully.")
        return response

class NotificationListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = Notification
    template_name = 'superadmin_dashboard/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('superadmin_dashboard:notification_list')


class AdminMessageInboxView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = DirectMessage
    template_name = 'superadmin_dashboard/admin_inbox.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return DirectMessage.objects.filter(recipient=self.request.user)

class AdminMessageSentView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = DirectMessage
    template_name = 'superadmin_dashboard/admin_sent_messages.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return DirectMessage.objects.filter(sender=self.request.user)

class AdminSendMessageView(LoginRequiredMixin, SuperAdminRequiredMixin, CreateView):
    model = DirectMessage
    form_class = DirectMessageForm
    template_name = 'superadmin_dashboard/send_message.html'
    success_url = reverse_lazy('superadmin_dashboard:admin_inbox')

    def form_valid(self, form):
        recipient_id = self.kwargs.get('instructor_id')
        recipient = get_object_or_404(User, id=recipient_id)
        form.instance.sender = self.request.user
        form.instance.recipient = recipient
        response = super().form_valid(form)
        log_action(self.request.user, f"Sent message to {recipient.username}", "DirectMessage", self.object.id, request=self.request)
        messages.success(self.request, f"Message sent to {recipient.get_full_name()}.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recipient'] = get_object_or_404(User, id=self.kwargs.get('instructor_id'))
        return context

class AdminMessageDetailView(LoginRequiredMixin, SuperAdminRequiredMixin, TemplateView):
    template_name = 'superadmin_dashboard/message_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        message = get_object_or_404(DirectMessage, id=self.kwargs.get('pk'))
        if message.recipient == self.request.user:
            message.is_read = True
            message.save()
        context['direct_message'] = message # Avoid conflict with Django's messages
        return context

class AuditLogListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = AuditLog
    template_name = 'superadmin_dashboard/audit_logs.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        queryset = AuditLog.objects.all().select_related('user')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                models.Q(action__icontains=q) |
                models.Q(user__username__icontains=q) |
                models.Q(details__icontains=q)
            )
        return queryset
    