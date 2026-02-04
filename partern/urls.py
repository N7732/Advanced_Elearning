from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantPartnerViewSet,
    PublicPartnerViewSet,
    PartnerDashboardView,
    PartnerStudentListView,
    PartnerInstructorListView,
    PartnerCourseListView,
    SuperAdminPartnerListView,
    approve_partner,
    deactivate_partner,
)

# API Router
router = DefaultRouter()
router.register(r'tenant-partners', TenantPartnerViewSet, basename='tenant-partner')
router.register(r'public-partners', PublicPartnerViewSet, basename='public-partner')

app_name = 'partern'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Partner Dashboard
    path('dashboard/', PartnerDashboardView.as_view(), name='partner_dashboard'),
    path('dashboard/<int:partner_id>/students/', PartnerStudentListView.as_view(), name='partner_students'),
    path('dashboard/<int:partner_id>/instructors/', PartnerInstructorListView.as_view(), name='partner_instructors'),
    path('dashboard/<int:partner_id>/courses/', PartnerCourseListView.as_view(), name='partner_courses'),
    
    # Super Admin Views
    path('superadmin/partners/', SuperAdminPartnerListView.as_view(), name='superadmin_partner_list'),
    path('superadmin/partners/<int:partner_id>/approve/', approve_partner, name='approve_partner'),
    path('superadmin/partners/<int:partner_id>/deactivate/', deactivate_partner, name='deactivate_partner'),
]