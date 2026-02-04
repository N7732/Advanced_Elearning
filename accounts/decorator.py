from django.contrib.auth.models import User
from .models import Learner, Instructor
from django.shortcuts import redirect
from functools import wraps

def learner_required(view_func):
    """Decorator to require user to be a learner"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if hasattr(request.user, 'learner_profile'):
            return view_func(request, *args, **kwargs)
        return redirect('unauthorized')
    return _wrapped_view

def instructor_required(view_func):
    """Decorator to require user to be an instructor"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if hasattr(request.user, 'instructor_profile'):
            return view_func(request, *args, **kwargs)
        return redirect('unauthorized')
    return _wrapped_view

def get_user_profile(user):
    """Get the extended profile for a user"""
    if hasattr(user, 'extended_profile'):
        return user.extended_profile
    return None

def is_learner(user):
    """Check if user is a learner"""
    return hasattr(user, 'learner_profile')

def is_instructor(user):
    """Check if user is an instructor"""
    return hasattr(user, 'instructor_profile')

def get_instructor_by_partner(partner):
    """Get all instructors for a partner"""
    try:
        return Instructor.objects.filter(partner=partner)
    except Instructor.DoesNotExist:
        return None
    
def get_learner_by_email(email):
    """Get learner by user email"""
    try:
        user = User.objects.get(email=email)
        return user.learner_profile
    except (User.DoesNotExist, Learner.DoesNotExist):
        return None

def get_instructor_by_email(email):
    """Get instructor by user email"""
    try:
        user = User.objects.get(email=email)
        return user.instructor_profile
    except (User.DoesNotExist, Instructor.DoesNotExist):
        return None
    
def get_learners_enrolled_in_course(course):
    """Get all learners enrolled in a course"""
    return Learner.objects.filter(enrolled_courses=course)

def get_instructors_by_name(name):
    """Search instructors by name"""
    return Instructor.objects.filter(user__first_name__icontains=name) | \
           Instructor.objects.filter(user__last_name__icontains=name)

def get_learners_by_name(name):
    """Search learners by name"""
    return Learner.objects.filter(user__first_name__icontains=name) | \
           Learner.objects.filter(user__last_name__icontains=name)

def get_active_subscriptions(learner):
    """Get active subscriptions for a learner"""
    return learner.subscriptions.filter(active=True)

def is_admin(view_func):
    """Decorator to require user to be an admin (superuser)"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return redirect('unauthorized')
    return _wrapped_view

def user_is_authenticated(view_func):
    """Decorator to require user to be authenticated"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return redirect('accounts:login')
    return _wrapped_view

def user_is_learner_or_instructor(view_func):
    """Decorator to require user to be either a learner or an instructor"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if hasattr(request.user, 'learner_profile') or hasattr(request.user, 'instructor_profile'):
            return view_func(request, *args, **kwargs)
        return redirect('unauthorized')
    return _wrapped_view
