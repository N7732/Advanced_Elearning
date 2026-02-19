# views.py
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend # pyright: ignore[reportMissingModuleSource]
from .models import (
    Course, Module, Lesson, Quiz, Enrollment, 
    LessonProgress, QuizAttempt, Review, Certificate
)
from .Serializer import *
from .permission import IsInstructorOrReadOnly, IsEnrolledOrReadOnly

# ==================== Course Views ====================

class CourseListView(generics.ListCreateAPIView):
    """
    List all published courses or create a new course (instructors only)
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['difficulty_level', 'is_free', 'is_published', 'partner']
    search_fields = ['title', 'description', 'short_description']
    ordering_fields = ['created_at', 'title', 'total_enrollments', 'average_rating']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CourseCreateUpdateSerializer
        return CourseListSerializer
    
    def get_queryset(self):
        queryset = Course.objects.all()
        
        # Filter by published status for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)
        
        # Filter by instructor if specified
        instructor_id = self.request.query_params.get('instructor')
        if instructor_id:
            queryset = queryset.filter(instructor_id=instructor_id)
        
        # Add annotations for efficiency
        return queryset.select_related('instructor__user', 'partner').prefetch_related('modules')
    
    def perform_create(self, serializer):
        # Set instructor to current user if they are an instructor
        if hasattr(self.request.user, 'instructor_profile'):
            serializer.save(instructor=self.request.user.instructor_profile)
        else:
            raise PermissionDenied("You must be an instructor to create courses")

class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a course instance.
    """
    permission_classes = [IsInstructorOrReadOnly]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CourseCreateUpdateSerializer
        return CourseDetailSerializer
    
    def get_queryset(self):
        queryset = Course.objects.prefetch_related(
            'modules__lessons',
            'prerequisite_relations__prerequisite',
            'reviews__learner__user'
        ).select_related('instructor__user', 'partner')
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)
        
        return queryset
    
    def perform_destroy(self, instance):
        # Only instructor or staff can delete
        if not (self.request.user.is_staff or 
                (hasattr(self.request.user, 'instructor_profile') and 
                 instance.instructor == self.request.user.instructor_profile)):
            raise PermissionDenied("You don't have permission to delete this course")
        instance.delete()

# ==================== Module Views ====================

class ModuleListCreateView(generics.ListCreateAPIView):
    """
    List modules for a course or create new module
    """
    permission_classes = [IsInstructorOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ModuleCreateUpdateSerializer
        return ModuleListSerializer
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return Module.objects.filter(course_id=course_id).select_related('course')
    
    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        
        # Check permission
        if not (self.request.user.is_staff or 
                (hasattr(self.request.user, 'instructor_profile') and 
                 course.instructor == self.request.user.instructor_profile)):
            raise PermissionDenied("You don't have permission to add modules to this course")
        
        serializer.save(course=course)

class ModuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a module
    """
    permission_classes = [IsInstructorOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ModuleCreateUpdateSerializer
        return ModuleDetailSerializer
    
    def get_queryset(self):
        return Module.objects.select_related('course__instructor__user').prefetch_related(
            'lessons', 'quizzes'
        )

# ==================== Lesson Views ====================

class LessonListCreateView(generics.ListCreateAPIView):
    """
    List lessons for a module or create new lesson
    """
    permission_classes = [IsInstructorOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LessonCreateUpdateSerializer
        return LessonListSerializer
    
    def get_queryset(self):
        module_id = self.kwargs.get('module_id')
        return Lesson.objects.filter(module_id=module_id).order_by('order')
    
    def perform_create(self, serializer):
        module = get_object_or_404(Module, id=self.kwargs.get('module_id'))
        
        # Check permission
        if not (self.request.user.is_staff or 
                (hasattr(self.request.user, 'instructor_profile') and 
                 module.course.instructor == self.request.user.instructor_profile)):
            raise PermissionDenied("You don't have permission to add lessons to this module")
        
        serializer.save(module=module)

class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a lesson
    """
    permission_classes = [IsInstructorOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return LessonCreateUpdateSerializer
        return LessonDetailSerializer
    
    def get_queryset(self):
        return Lesson.objects.select_related(
            'module__course__instructor__user'
        ).prefetch_related('quizzes')

# ==================== Quiz Views ====================

class QuizListCreateView(generics.ListCreateAPIView):
    """
    List quizzes or create new quiz
    """
    permission_classes = [IsInstructorOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuizCreateUpdateSerializer
        return QuizListSerializer
    
    def get_queryset(self):
        queryset = Quiz.objects.all()
        
        # Filter by parent
        course_id = self.request.query_params.get('course')
        module_id = self.request.query_params.get('module')
        lesson_id = self.request.query_params.get('lesson')
        
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        elif module_id:
            queryset = queryset.filter(module_id=module_id)
        elif lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        
        return queryset.select_related('course', 'module', 'lesson')

class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a quiz
    """
    permission_classes = [IsInstructorOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return QuizCreateUpdateSerializer
        return QuizDetailSerializer
    
    def get_queryset(self):
        return Quiz.objects.prefetch_related('questions')

# ==================== Enrollment Views ====================

class EnrollmentListView(generics.ListCreateAPIView):
    """
    List user enrollments or enroll in a course
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EnrollmentCreateSerializer
        return EnrollmentSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Filter by user role
        if hasattr(user, 'learner_profile'):
            # Learners see their own enrollments
            queryset = Enrollment.objects.filter(learner=user.learner_profile)
        elif hasattr(user, 'instructor_profile'):
            # Instructors see enrollments for their courses
            queryset = Enrollment.objects.filter(course__instructor=user.instructor_profile)
        elif user.is_staff:
            # Staff see all enrollments
            queryset = Enrollment.objects.all()
        else:
            queryset = Enrollment.objects.none()
        
        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related(
            'learner__user', 'course', 'organization'
        ).order_by('-enrolled_at')
    
    def perform_create(self, serializer):
        # Create enrollment with current learner
        serializer.save()

class EnrollmentDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update enrollment details
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EnrollmentSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if hasattr(user, 'learner_profile'):
            return Enrollment.objects.filter(learner=user.learner_profile)
        elif hasattr(user, 'instructor_profile'):
            return Enrollment.objects.filter(course__instructor=user.instructor_profile)
        elif user.is_staff:
            return Enrollment.objects.all()
        
        return Enrollment.objects.none()

class MyLearningView(generics.ListAPIView):
    """
    Get current user's learning progress (enrolled courses with progress)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EnrollmentSerializer
    
    def get_queryset(self):
        if not hasattr(self.request.user, 'learner_profile'):
            return Enrollment.objects.none()
        
        return Enrollment.objects.filter(
            learner=self.request.user.learner_profile
        ).select_related('course', 'current_lesson').order_by('-last_accessed')

# ==================== Lesson Progress Views ====================

class LessonProgressView(generics.RetrieveUpdateAPIView):
    """
    Track progress for a specific lesson
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return LessonProgressUpdateSerializer
        return LessonProgressSerializer
    
    def get_object(self):
        lesson_id = self.kwargs.get('lesson_id')
        user = self.request.user
        
        if not hasattr(user, 'learner_profile'):
            raise PermissionDenied("Only learners can track progress")
        
        # Get or create progress record
        progress, created = LessonProgress.objects.get_or_create(
            learner=user.learner_profile,
            lesson_id=lesson_id
        )
        
        return progress

class LessonProgressBatchUpdateView(generics.GenericAPIView):
    """
    Batch update multiple lessons progress (e.g., mark module as completed)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, 'learner_profile'):
            return Response(
                {"error": "Only learners can update progress"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        lesson_ids = request.data.get('lesson_ids', [])
        mark_completed = request.data.get('completed', True)
        
        if not lesson_ids:
            return Response(
                {"error": "lesson_ids required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = []
        for lesson_id in lesson_ids:
            progress, _ = LessonProgress.objects.get_or_create(
                learner=request.user.learner_profile,
                lesson_id=lesson_id
            )
            
            if mark_completed and not progress.is_completed:
                progress.is_completed = True
                progress.completed_at = timezone.now()
                progress.save()
                updated.append(lesson_id)
        
        return Response({
            "message": f"Updated {len(updated)} lessons",
            "updated": updated
        })

# ==================== Quiz Attempt Views ====================

class QuizAttemptCreateView(generics.CreateAPIView):
    """
    Start a new quiz attempt
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuizAttemptSerializer
    
    def perform_create(self, serializer):
        quiz_id = self.kwargs.get('quiz_id')
        user = self.request.user
        
        if not hasattr(user, 'learner_profile'):
            raise PermissionDenied("Only learners can take quizzes")
        
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Check enrollment for course-related quizzes
        if quiz.course:
            if not Enrollment.objects.filter(
                learner=user.learner_profile,
                course=quiz.course,
                status='active'
            ).exists():
                raise PermissionDenied("You must be enrolled to take this quiz")
        
        # Get attempt number
        attempt_count = QuizAttempt.objects.filter(
            quiz=quiz,
            learner=user.learner_profile
        ).count()
        
        if attempt_count >= quiz.max_attempts:
            raise ValidationError("Maximum attempts reached")
        
        serializer.save(
            quiz=quiz,
            learner=user.learner_profile,
            attempt_number=attempt_count + 1
        )

class QuizAttemptDetailView(generics.RetrieveAPIView):
    """
    Get quiz attempt details
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuizAttemptSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if hasattr(user, 'learner_profile'):
            return QuizAttempt.objects.filter(learner=user.learner_profile)
        elif hasattr(user, 'instructor_profile'):
            return QuizAttempt.objects.filter(quiz__course__instructor=user.instructor_profile)
        elif user.is_staff:
            return QuizAttempt.objects.all()
        
        return QuizAttempt.objects.none()

class QuizAnswerSubmitView(generics.GenericAPIView):
    """
    Submit answers for a quiz attempt
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuizAnswerSubmitSerializer
    
    def post(self, request, *args, **kwargs):
        attempt_id = self.kwargs.get('attempt_id')
        
        try:
            attempt = QuizAttempt.objects.get(
                id=attempt_id,
                learner=request.user.learner_profile,
                completed_at__isnull=True
            )
        except QuizAttempt.DoesNotExist:
            return Response(
                {"error": "Active quiz attempt not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(quiz_attempt=attempt)
        
        return Response(
            QuizAttemptSerializer(attempt, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK
        )

# ==================== Review Views ====================

class CourseReviewListView(generics.ListCreateAPIView):
    """
    List reviews for a course or create a new review
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating']
    
    def get_serializer_class(self):
        return ReviewSerializer
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return Review.objects.filter(course_id=course_id).select_related(
            'learner__user'
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        
        if not hasattr(self.request.user, 'learner_profile'):
            raise PermissionDenied("Only learners can review courses")
        
        # Check if enrolled and completed
        enrollment = Enrollment.objects.filter(
            learner=self.request.user.learner_profile,
            course=course
        ).first()
        
        if not enrollment:
            raise PermissionDenied("You must be enrolled to review this course")
        
        serializer.save(
            course=course,
            learner=self.request.user.learner_profile,
            enrollment=enrollment
        )

# ==================== Certificate Views ====================

class CertificateListView(generics.ListAPIView):
    """
    List certificates for current user
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CertificateSerializer
    
    def get_queryset(self):
        if hasattr(self.request.user, 'learner_profile'):
            return Certificate.objects.filter(
                enrollment__learner=self.request.user.learner_profile
            ).select_related('enrollment__learner__user', 'enrollment__course')
        return Certificate.objects.none()

class CertificateDetailView(generics.RetrieveAPIView):
    """
    Get certificate details
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CertificateSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if hasattr(user, 'learner_profile'):
            return Certificate.objects.filter(enrollment__learner=user.learner_profile)
        elif user.is_staff:
            return Certificate.objects.all()
        
        return Certificate.objects.none()

class CertificateVerifyView(generics.GenericAPIView):
    """
    Public endpoint to verify a certificate
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = CertificateSerializer
    
    def get(self, request, hash_value):
        try:
            certificate = Certificate.objects.get(verification_hash=hash_value)
            serializer = self.get_serializer(certificate)
            return Response(serializer.data)
        except Certificate.DoesNotExist:
            return Response(
                {"error": "Invalid certificate hash"},
                status=status.HTTP_404_NOT_FOUND
            )

# ==================== Dashboard/Stats Views ====================

class InstructorDashboardView(generics.GenericAPIView):
    """
    Get instructor dashboard statistics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, 'instructor_profile'):
            return Response(
                {"error": "Only instructors can access this dashboard"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instructor = request.user.instructor_profile
        
        # Get courses
        courses = Course.objects.filter(instructor=instructor)
        
        # Calculate stats
        total_students = Enrollment.objects.filter(course__in=courses).count()
        active_students = Enrollment.objects.filter(
            course__in=courses, 
            status='active'
        ).count()
        total_revenue = courses.filter(is_free=False).aggregate(
            total=models.Sum('price')
        )['total'] or 0
        
        recent_enrollments = Enrollment.objects.filter(
            course__in=courses
        ).select_related('learner__user', 'course').order_by('-enrolled_at')[:10]
        
        return Response({
            'total_courses': courses.count(),
            'published_courses': courses.filter(is_published=True).count(),
            'total_students': total_students,
            'active_students': active_students,
            'total_revenue': total_revenue,
            'recent_enrollments': EnrollmentSerializer(recent_enrollments, many=True).data
        })