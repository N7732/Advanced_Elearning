from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LearnerViewSet,
    InstructorViewSet,
    about_as,
    contact_as,
    instructor_edit_profile,
    learner_edit_profile,
    learner_register,
    instructor_register,
    user_login,
    user_logout,
    profile,
)

# API Router
router = DefaultRouter()
router.register(r'learners', LearnerViewSet, basename='learner')
router.register(r'instructors', InstructorViewSet, basename='instructor')

app_name = 'accounts'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Authentication
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    
    # Registration
    path('register/learner/', learner_register, name='learner_register'),
    path('register/learner/<uuid:token>/', learner_register, name='learner_register_invite'),
    path('register/instructor/', instructor_register, name='instructor_register'), # Keep this for named reverse matching if needed, but it checks for token internally? No, I should make it require token in path.
    path('register/instructor/<uuid:token>/', instructor_register, name='instructor_register_invite'),
    
    # Profile
    path('profile/', profile, name='profile'),

    # Static Pages
    path('about/', about_as, name='about'),
    path('contact/', contact_as, name='contact'),

    #profile update
    path('profile/edit/', learner_edit_profile, name='edit_profile'),
    path('profile/edit/instructor/', instructor_edit_profile, name='edit_profile_instructor'),
]
