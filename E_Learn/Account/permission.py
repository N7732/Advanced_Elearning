# permissions.py
from rest_framework import permissions

class IsLearner(permissions.BasePermission):
    """
    Permission for learner users only
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_learner

class IsInstructor(permissions.BasePermission):
    """
    Permission for instructor users only
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_instructor

class IsAdmin(permissions.BasePermission):
    """
    Permission for admin users only
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.user == request.user

class IsProfileOwner(permissions.BasePermission):
    """
    Permission for profile owners
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class CanManageSubscription(permissions.BasePermission):
    """
    Permission for managing subscriptions (admin only)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin or request.user.is_staff
        )