# partner/permissions.py
from rest_framework import permissions
from .models import Partner

class IsSuperAdminOrPartnerAdmin(permissions.BasePermission):
    """
    Allow access to superadmins or partner admins
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Superadmin can do anything
        if request.user.is_superuser or hasattr(request.user, 'superadmin_profile'):
            return True
        
        # Check if user is partner admin
        if hasattr(obj, 'partner'):
            # Object has direct partner reference
            return request.user.partner_admin_relations.filter(partner=obj.partner).exists()
        
        if isinstance(obj, Partner):
            return request.user.partner_admin_relations.filter(partner=obj).exists()
        
        return False


class IsPartnerAdmin(permissions.BasePermission):
    """
    Allow access only to partner admins
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.partner_admin_relations.exists()


class CanManagePartner(permissions.BasePermission):
    """
    Check if user can manage a specific partner
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Superadmin can manage any partner
        if request.user.is_superuser or hasattr(request.user, 'superadmin_profile'):
            return True
        
        # Get partner from different object types
        if isinstance(obj, Partner):
            partner = obj
        elif hasattr(obj, 'partner'):
            partner = obj.partner
        elif hasattr(obj, 'campus') and hasattr(obj.campus, 'partner'):
            partner = obj.campus.partner
        elif hasattr(obj, 'faculty') and hasattr(obj.faculty, 'campus') and hasattr(obj.faculty.campus, 'partner'):
            partner = obj.faculty.campus.partner
        else:
            return False
        
        # Check if user is partner admin
        return request.user.partner_admin_relations.filter(partner=partner).exists()