# core/middleware.py
import re
from django.http import HttpResponseForbidden
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import logout
import logging

logger = logging.getLogger(__name__)

class RestrictAdminIPMiddleware:
    """Restrict admin access to specific IPs"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if accessing admin or superadmin paths
        if request.path.startswith('/admin/') or request.path.startswith('/api/superadmin/'):
            allowed_ips = getattr(settings, 'ALLOWED_ADMIN_IPS', [])
            
            if allowed_ips:
                client_ip = self._get_client_ip(request)
                
                # Allow localhost always
                if client_ip not in ['127.0.0.1', '::1'] and client_ip not in allowed_ips:
                    logger.warning(f'Blocked admin access from IP: {client_ip}')
                    return HttpResponseForbidden('Access denied from this IP address')
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class SecurityHeadersMiddleware:
    """Add security headers to all responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class AuditLogMiddleware:
    """Log all important actions"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log important actions
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            if request.path.startswith('/api/superadmin/'):
                self._log_admin_action(request)
        
        return response
    
    def _log_admin_action(self, request):
        from SuperAdmin.models import AuditLog
        
        AuditLog.objects.create(
            user=request.user,
            action=request.method,
            action_description=f'{request.method} {request.path}',
            target_model='API',
            target_id=0,
            target_repr=request.path,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'data': str(getattr(request, 'data', {}))}
        )
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class SessionSecurityMiddleware:
    """Enforce session security"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if session is expired
            last_activity = request.session.get('last_activity')
            timeout = getattr(settings, 'SESSION_TIMEOUT_MINUTES', 30) * 60
            
            if last_activity:
                elapsed = timezone.now().timestamp() - last_activity
                if elapsed > timeout:
                    logout(request)
                    return HttpResponseForbidden('Session expired. Please login again.')
            
            # Update last activity
            request.session['last_activity'] = timezone.now().timestamp()
        
        return self.get_response(request)