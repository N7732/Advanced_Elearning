# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'account'

# Using ViewSets for more complex CRUD operations
# router = DefaultRouter()
# router.register(r'learners', views.LearnerProfileViewSet)
# router.register(r'instructors', views.InstructorProfileViewSet)

urlpatterns = [
    # Authentication
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    
    # User
    path('user/', views.UserDetailView.as_view(), name='user-detail'),
    
    # Learner Profiles
    path('learners/', views.LearnerProfileListView.as_view(), name='learner-list'),
    path('learners/me/', views.CurrentLearnerProfileView.as_view(), name='current-learner'),
    path('learners/<int:pk>/', views.LearnerProfileDetailView.as_view(), name='learner-detail'),
    
    # Instructor Profiles
    path('instructors/', views.InstructorProfileListView.as_view(), name='instructor-list'),
    path('instructors/me/', views.CurrentInstructorProfileView.as_view(), name='current-instructor'),
    path('instructors/<int:pk>/', views.InstructorProfileDetailView.as_view(), name='instructor-detail'),
    
    # Subscriptions
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscription-list'),
    path('subscriptions/me/', views.UserSubscriptionView.as_view(), name='user-subscription'),
    path('subscriptions/<int:pk>/', views.SubscriptionDetailView.as_view(), name='subscription-detail'),
    
    # Account Profile
    path('profile/', views.AccountProfileDetailView.as_view(), name='account-profile'),
]