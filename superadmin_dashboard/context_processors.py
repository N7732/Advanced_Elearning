from .models import Notification, DirectMessage

def global_context_data(request):
    """
    Context processor for notifications and direct messages accessible to authenticated users.
    """
    if request.user.is_authenticated:
        # Base counts for any authenticated user
        unread_messages_count = DirectMessage.objects.filter(recipient=request.user, is_read=False).count()
        
        context = {
            'unread_messages_count': unread_messages_count,
        }
        
        # Superadmin specific data
        if request.user.is_superuser:
            unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
            context['unread_notifications_count'] = unread_notifications.count()
            context['recent_notifications'] = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        return context
        
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'unread_messages_count': 0
    }
