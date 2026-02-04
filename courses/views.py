from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .models import Course, Module, Lesson, Quizes
from .serializer import CourseSerializer, ModuleSerializer, LessonSerializer, QuizesSerializer  
from rest_framework import viewsets
from django.contrib.auth.decorators import login_required
from accounts.decorator import learner_required, instructor_required, user_is_authenticated, user_is_learner_or_instructor, is_admin

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Course, Module, Lesson, Quizes, Enrollment, Certificate
from .serializer import (
    CourseSerializer, ModuleSerializer, LessonSerializer, QuizesSerializer,
    EnrollmentSerializer, CertificateSerializer
)

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user
        
        # Check if already enrolled
        learner = getattr(user, 'learner_profile', None)
        if not learner:
             return Response({'error': 'User is not a learner'}, status=status.HTTP_400_BAD_REQUEST)

        if Enrollment.objects.filter(learner=learner, course=course).exists():
             return Response({'message': 'Already enrolled'}, status=status.HTTP_400_BAD_REQUEST)

        # Check prerequisites
        # Optimization: prefetch prerequisites
        prereqs = course.prerequisite_requirements.all()
        for prereq in prereqs:
            required_course = prereq.prerequisite_course
            min_score = prereq.min_score
            
            # Check if user enrolled in required course
            try:
                enrollment = Enrollment.objects.get(learner=learner, course=required_course)
                if enrollment.score < min_score:
                    return Response({
                        'error': f'Prerequisite not met. You need {min_score} marks in {required_course.title}. Current score: {enrollment.score}'
                    }, status=status.HTTP_403_FORBIDDEN)
            except Enrollment.DoesNotExist:
                return Response({
                    'error': f'Prerequisite not met. You must complete {required_course.title} first.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Enroll
        Enrollment.objects.create(learner=learner, course=course)
        return Response({'status': 'Enrolled successfully'}, status=status.HTTP_201_CREATED)

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

class QuizesViewSet(viewsets.ModelViewSet):
    queryset = Quizes.objects.all()
    serializer_class = QuizesSerializer

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        learner = getattr(self.request.user, 'learner_profile', None)
        if learner:
            return Enrollment.objects.filter(learner=learner)
        return Enrollment.objects.none()

class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        learner = getattr(self.request.user, 'learner_profile', None)
        if learner:
             return Certificate.objects.filter(enrollment__learner=learner)
        return Certificate.objects.none()

# Create your views here.

def course(request):
    return render(request, 'courses/course.html')

@login_required
@instructor_required
@user_is_authenticated
def create_course(request):
    if request.method == 'POST':
        course_title = request.POST.get('title')
        course_description = request.POST.get('description')
        is_free = request.POST.get('is_free') == 'on'
        price = request.POST.get('price') if not is_free else 0
        currency = request.POST.get('currency')

        if course_title and course_description:
            Course.objects.create(
                title=course_title,
                description=course_description,
                is_free=is_free,
                price=price,
                currency=currency
            )
            return HttpResponse("Course created successfully!")
        if 'thumbnail' in request.FILES:
            course = Course.objects.get(title=course_title)
            thumbnail = request.FILES['thumbnail']
            course.thumbnail = thumbnail
            course.save()


        lesson_count = int(request.POST.get('lesson_count', 0))
        course = Course.objects.get(title=course_title)
        for i in range(1, lesson_count + 1):
            module_title = request.POST.get(f'module_{i}_title')
            module_description = request.POST.get(f'module_{i}_description')
            if module_title and module_description:
                Module.objects.create(
                    course=course,
                    title=module_title,
                    description=module_description,
                    order=i
                )

    return render(request, 'courses/create_course.html')

def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})

@login_required
def course_detail(request, course_id):
    course = Course.objects.get(id=course_id)
    course = get_object_or_404(Course, id=course_id)
    lessons = course.Lessons.all().order_by('order')
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'lessons': lessons
    })

@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'courses/lesson_detail.html', {
        'lesson': lesson
    })

@login_required

@user_is_authenticated
@user_is_learner_or_instructor
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quizes, id=quiz_id)
    return render(request, 'courses/quiz_detail.html', {
        'quiz': quiz
    })


from partern.models import TenantPartner
from django.db.models import Q
from django.utils import timezone

def home(request):
    active_partners = TenantPartner.objects.filter(
        active=True
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=timezone.now().date())
    )
    return render(request, 'courses/home.html', {'partners': active_partners})

