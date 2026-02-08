from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from .models import User, Learner, Instructor, AccountProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Always ensure AccountProfile exists
    AccountProfile.objects.get_or_create(user=instance)
    
    # Ensure specific profile exists based on type, even if not created (updated)
    # Ensure specific profile exists based on type, even if not created (updated)
    # if instance.user_type == 'learner':
    #     Learner.objects.get_or_create(user=instance)
    if instance.user_type == 'instructor':
        # Instructor.objects.get_or_create(user=instance)
        configure_instructor_permissions(instance)

def configure_instructor_permissions(user):
    """
    Grants instructor permissions by:
    1. Setting is_staff=True for admin access
    2. Adding user to 'Instructors' group with Course permissions
    """
    # 1. Enable Admin Access
    if not user.is_staff:
        # Use update to avoid triggering signals recursively
        User.objects.filter(pk=user.pk).update(is_staff=True)
        # Update local instance to match
        user.is_staff = True

    # 2. Setup Instructors Group
    group, group_created = Group.objects.get_or_create(name='Instructors')
    
    # If group was just created OR has no permissions, assign permissions
    if group_created or not group.permissions.exists():
        course_models = ['Course', 'Module', 'Lesson', 'Quizes', 'QuizQuestion', 'CoursePrerequisite']
        permissions_to_add = []
        
        for model_name in course_models:
            try:
                model = apps.get_model('courses', model_name)
                content_type = ContentType.objects.get_for_model(model)
                # Get all permissions for this model (add, change, delete, view)
                perms = Permission.objects.filter(content_type=content_type)
                permissions_to_add.extend(perms)
            except LookupError:
                # Model might not be available yet or name is incorrect
                continue
        
        if permissions_to_add:
            group.permissions.add(*permissions_to_add)

    # 3. Add user to group
    if not user.groups.filter(name='Instructors').exists():
        user.groups.add(group)
