# superadmin/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'superadmin'

urlpatterns = [
    # Authentication
    path('auth/login/', views.SuperAdminLoginView.as_view(), name='superadmin-login'),
    
    # SuperAdmin Profile
    path('profile/', views.SuperAdminProfileView.as_view(), name='superadmin-profile'),
    path('create/', views.SuperAdminCreateView.as_view(), name='superadmin-create'),
    
    # Dashboard
    path('dashboard/', views.SuperAdminDashboardView.as_view(), name='dashboard'),
    path('system-health/', views.SystemHealthView.as_view(), name='system-health'),
    
    # Admin Management
    path('admins/', views.AdminListView.as_view(), name='admin-list'),
    path('admins/<int:pk>/', views.AdminDetailView.as_view(), name='admin-detail'),
    path('admins/<int:pk>/toggle-status/', views.AdminActivateView.as_view(), name='admin-toggle-status'),
    
    # Independent Instructor Management
    path('instructors/', views.IndependentInstructorListView.as_view(), name='instructor-list'),
    path('instructors/<int:pk>/', views.IndependentInstructorDetailView.as_view(), name='instructor-detail'),
    path('instructors/<int:pk>/verify/', views.InstructorVerificationView.as_view(), name='instructor-verify'),
    
    # Partner Management
    path('partners/', views.PartnerListView.as_view(), name='partner-list'),
    path('partners/<int:pk>/', views.PartnerDetailView.as_view(), name='partner-detail'),
    path('partners/<int:pk>/verify/', views.PartnerVerifyView.as_view(), name='partner-verify'),
    path('partners/<int:pk>/add-admins/', views.PartnerAdminAddView.as_view(), name='partner-add-admins'),
    
    # Partner Instructors
    path('partners/<int:partner_id>/instructors/', views.PartnerInstructorListView.as_view(), name='partner-instructor-list'),
    
    # System Settings
    path('settings/global/', views.GlobalSettingView.as_view(), name='global-settings'),
    path('settings/features/', views.PlatformFeatureListView.as_view(), name='feature-list'),
    path('settings/features/<int:pk>/', views.PlatformFeatureDetailView.as_view(), name='feature-detail'),
    
    # Announcements
    path('announcements/', views.SystemAnnouncementListView.as_view(), name='announcement-list'),
    path('announcements/<int:pk>/', views.SystemAnnouncementDetailView.as_view(), name='announcement-detail'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/create/', views.NotificationCreateView.as_view(), name='notification-create'),
    
    # Messages
    path('messages/', views.DirectMessageListView.as_view(), name='message-list'),
    path('messages/<int:pk>/', views.DirectMessageDetailView.as_view(), name='message-detail'),
    
    # Audit Logs
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-log-list'),
    path('audit-logs/<int:pk>/', views.AuditLogDetailView.as_view(), name='audit-log-detail'),
    
    # Reports
    path('reports/', views.SystemReportListView.as_view(), name='report-list'),
    path('reports/<int:pk>/', views.SystemReportDetailView.as_view(), name='report-detail'),
    
    # Backups
    path('backups/', views.BackupListView.as_view(), name='backup-list'),
    path('backups/<int:pk>/', views.BackupDetailView.as_view(), name='backup-detail'),
]