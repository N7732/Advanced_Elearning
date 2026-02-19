# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'courses'

# Using APIView classes instead of ViewSets for more control
urlpatterns = [
    # Course endpoints
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='course-detail'),
    
    # Module endpoints
    path('courses/<int:course_id>/modules/', views.ModuleListCreateView.as_view(), name='module-list'),
    path('modules/<int:pk>/', views.ModuleDetailView.as_view(), name='module-detail'),
    
    # Lesson endpoints
    path('modules/<int:module_id>/lessons/', views.LessonListCreateView.as_view(), name='lesson-list'),
    path('lessons/<int:pk>/', views.LessonDetailView.as_view(), name='lesson-detail'),
    
    # Quiz endpoints
    path('quizzes/', views.QuizListCreateView.as_view(), name='quiz-list'),
    path('quizzes/<int:pk>/', views.QuizDetailView.as_view(), name='quiz-detail'),
    
    # Enrollment endpoints
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/<int:pk>/', views.EnrollmentDetailView.as_view(), name='enrollment-detail'),
    path('my-learning/', views.MyLearningView.as_view(), name='my-learning'),
    
    # Progress endpoints
    path('lessons/<int:lesson_id>/progress/', views.LessonProgressView.as_view(), name='lesson-progress'),
    path('progress/batch-update/', views.LessonProgressBatchUpdateView.as_view(), name='progress-batch'),
    
    # Quiz attempt endpoints
    path('quizzes/<int:quiz_id>/attempts/', views.QuizAttemptCreateView.as_view(), name='quiz-attempt-create'),
    path('attempts/<int:attempt_id>/', views.QuizAttemptDetailView.as_view(), name='quiz-attempt-detail'),
    path('attempts/<int:attempt_id>/submit/', views.QuizAnswerSubmitView.as_view(), name='quiz-submit'),
    
    # Review endpoints
    path('courses/<int:course_id>/reviews/', views.CourseReviewListView.as_view(), name='course-reviews'),
    
    # Certificate endpoints
    path('certificates/', views.CertificateListView.as_view(), name='certificate-list'),
    path('certificates/<int:pk>/', views.CertificateDetailView.as_view(), name='certificate-detail'),
    path('verify-certificate/<str:hash_value>/', views.CertificateVerifyView.as_view(), name='certificate-verify'),
    
    # Dashboard
    path('instructor/dashboard/', views.InstructorDashboardView.as_view(), name='instructor-dashboard'),
]