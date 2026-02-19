# permissions.py
from rest_framework import permissions
from .models import Enrollment, Course, Lesson

class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow instructors to edit their courses.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for authenticated users
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Staff can do anything
        if request.user.is_staff:
            return True
        
        # Check if user is instructor of this course
        if hasattr(obj, 'instructor'):
            return obj.instructor == getattr(request.user, 'instructor_profile', None)
        
        # For nested objects (Module, Lesson, etc.)
        if hasattr(obj, 'course') and hasattr(obj.course, 'instructor'):
            return obj.course.instructor == getattr(request.user, 'instructor_profile', None)
        
        return False

class IsEnrolledOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow enrolled learners to access course content.
    """
    def has_permission(self, request, view):
        # Allow anyone to list/view courses
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Allow anyone to view course details
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Staff can do anything
        if request.user.is_staff:
            return True
        
        # For course objects, check enrollment
        if isinstance(obj, Course):
            if hasattr(request.user, 'learner_profile'):
                return Enrollment.objects.filter(
                    learner=request.user.learner_profile,
                    course=obj,
                    status='active'
                ).exists()
        
        # For lessons, check course enrollment
        if isinstance(obj, Lesson):
            if hasattr(request.user, 'learner_profile'):
                return Enrollment.objects.filter(
                    learner=request.user.learner_profile,
                    course=obj.module.course,
                    status='active'
                ).exists()
        
        return False