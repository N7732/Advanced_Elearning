from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, ModuleViewSet, LessonViewSet, QuizesViewSet,
    EnrollmentViewSet, CertificateViewSet,
    home, course, create_course, course_list, course_detail, 
    lesson_detail, quiz_detail
)

router = DefaultRouter()
router.register(r'api/courses', CourseViewSet)
router.register(r'api/modules', ModuleViewSet)
router.register(r'api/lessons', LessonViewSet)
router.register(r'api/quizes', QuizesViewSet)
router.register(r'api/enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'api/certificates', CertificateViewSet, basename='certificate')

urlpatterns = [
    # HTML Views
    path('', home, name='home'),
    path('course/', course, name='course'),
    path('create-course/', create_course, name='create_course'),
    path('courses/', course_list, name='course_list'),
    path('course/<int:course_id>/', course_detail, name='course_detail'),
    path('lesson/<int:lesson_id>/', lesson_detail, name='lesson_detail'),
    path('quiz/<int:quiz_id>/', quiz_detail, name='quiz_detail'),
    
    # API Views
    path('', include(router.urls)),
]