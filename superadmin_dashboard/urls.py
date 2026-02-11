from django.urls import path
from .views import (
    OverviewView, TenantListView, TenantCreateView, TenantUpdateView, 
    LearnerListView, InstructorListView, AdminUserListView, GlobalCourseListView,
    toggle_tenant_status, toggle_rdb_approval, toggle_instructor_approval,
    GlobalSettingsView, NotificationListView, mark_notification_read,
    AdminMessageInboxView, AdminMessageSentView, AdminSendMessageView, AdminMessageDetailView,
    AuditLogListView
)

app_name = 'superadmin_dashboard'

urlpatterns = [
    path('overview/', OverviewView.as_view(), name='overview'),
    
    # Tenants
    path('tenants/', TenantListView.as_view(), name='tenant_list'),
    path('tenants/courses/', GlobalCourseListView.as_view(), name='global_course_list'),
    path('tenants/create/', TenantCreateView.as_view(), name='tenant_create'),
    path('tenants/<int:pk>/edit/', TenantUpdateView.as_view(), name='tenant_edit'),
    path('tenants/<int:pk>/toggle-status/', toggle_tenant_status, name='toggle_tenant_status'),
    path('tenants/<int:pk>/toggle-rdb/', toggle_rdb_approval, name='toggle_rdb_approval'),
    
    # Users
    path('learners/', LearnerListView.as_view(), name='learner_list'),
    path('instructors/', InstructorListView.as_view(), name='instructor_list'),
    path('instructors/<int:pk>/toggle-approval/', toggle_instructor_approval, name='toggle_instructor_approval'),
    path('admins/', AdminUserListView.as_view(), name='admin_user_list'),
    
    # System
    path('settings/', GlobalSettingsView.as_view(), name='global_settings'),
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/read/', mark_notification_read, name='mark_notification_read'),
    
    path('', OverviewView.as_view(), name='index'),

    # Messaging
    path('messages/inbox/', AdminMessageInboxView.as_view(), name='admin_inbox'),
    path('messages/sent/', AdminMessageSentView.as_view(), name='admin_sent_messages'),
    path('messages/send/<int:instructor_id>/', AdminSendMessageView.as_view(), name='admin_send_message'),
    path('messages/<int:pk>/', AdminMessageDetailView.as_view(), name='admin_message_detail'),
    path('audit-logs/', AuditLogListView.as_view(), name='audit_logs'),
]
