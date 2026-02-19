# superadmin/permissions.py
from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """
    Custom permission to only allow superadmins to access.
    Checks for both Django superuser and custom SuperAdmin profile.
    """
    
    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django superusers have full access
        if request.user.is_superuser:
            return True
        
        # Check for custom superadmin profile
        return hasattr(request.user, 'superadmin_profile')
    
    def has_object_permission(self, request, view, obj):
        # Same as has_permission for object-level
        return self.has_permission(request, view)


class IsSuperAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to anyone, but write access only to superadmins.
    """
    
    def has_permission(self, request, view):
        # Allow any safe methods
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write methods, check superadmin
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        return hasattr(request.user, 'superadmin_profile')