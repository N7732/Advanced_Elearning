# partner/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'partner'

urlpatterns = [
    # Public endpoints (no auth required)
    path('public/', views.PublicPartnerListView.as_view(), name='public-partner-list'),
    path('public/<slug:slug>/', views.PublicPartnerDetailView.as_view(), name='public-partner-detail'),
    
    # Invitation acceptance (public)
    path('invitations/accept/<uuid:token>/', views.AcceptInvitationView.as_view(), name='accept-invitation'),
    
    # Partner management (authenticated)
    path('', views.PartnerListView.as_view(), name='partner-list'),
    path('<slug:slug>/', views.PartnerDetailView.as_view(), name='partner-detail'),
    path('<slug:slug>/verify/', views.PartnerVerificationView.as_view(), name='partner-verify'),
    path('<slug:slug>/dashboard/', views.PartnerDashboardView.as_view(), name='partner-dashboard'),
    
    # Admin management
    path('<slug:slug>/admins/', views.PartnerAdminListView.as_view(), name='partner-admin-list'),
    path('admins/<int:pk>/', views.PartnerAdminDetailView.as_view(), name='partner-admin-detail'),
    
    # Instructor management
    path('<slug:slug>/instructors/', views.PartnerInstructorListView.as_view(), name='partner-instructor-list'),
    path('instructors/<int:pk>/', views.PartnerInstructorDetailView.as_view(), name='partner-instructor-detail'),
    
    # Campus management
    path('<slug:slug>/campuses/', views.CampusListView.as_view(), name='campus-list'),
    path('campuses/<uuid:pk>/', views.CampusDetailView.as_view(), name='campus-detail'),
    
    # Faculty management
    path('campuses/<uuid:campus_id>/faculties/', views.FacultyListView.as_view(), name='faculty-list'),
    path('faculties/<uuid:pk>/', views.FacultyDetailView.as_view(), name='faculty-detail'),
    
    # Department management
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('departments/<uuid:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    
    # Document management
    path('<slug:slug>/documents/', views.PartnerDocumentListView.as_view(), name='document-list'),
    path('documents/<int:pk>/', views.PartnerDocumentDetailView.as_view(), name='document-detail'),
    path('<slug:slug>/documents/<int:pk>/verify/', views.PartnerDocumentVerifyView.as_view(), name='document-verify'),
    
    # Invitation management
    path('<slug:slug>/invitations/', views.PartnerInvitationListView.as_view(), name='invitation-list'),
    path('invitations/<int:pk>/', views.PartnerInvitationDetailView.as_view(), name='invitation-detail'),
    
    # Activity logs
    path('<slug:slug>/activities/', views.PartnerActivityLogListView.as_view(), name='activity-list'),
    
    # Subscriptions
    path('<slug:slug>/subscriptions/', views.PartnerSubscriptionListView.as_view(), name='subscription-list'),
    path('subscriptions/<int:pk>/', views.PartnerSubscriptionDetailView.as_view(), name='subscription-detail'),
]