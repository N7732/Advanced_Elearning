from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LearnerViewSet,
    InstructorViewSet,
    Learner_register,
    Instructor_register,
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
    path('register/learner/', Learner_register, name='learner_register'),
    path('register/instructor/', Instructor_register, name='instructor_register'),
    
    # Profile
    path('profile/', profile, name='profile'),
]
