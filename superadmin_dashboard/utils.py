from .models import AuditLog

def log_action(user, action, target_model=None, target_id=None, details=None, request=None):
    """
    Standardized function to log administrative actions.
    """
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        user=user,
        action=action,
        target_model=target_model,
        target_id=target_id,
        ip_address=ip_address,
        details=details
    )
