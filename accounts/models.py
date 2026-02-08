from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('learner', 'Learner'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)

    @property
    def is_learner(self):
        return self.user_type == 'learner'

    @property
    def is_instructor(self):
        return self.user_type == 'instructor'
    
    @property
    def is_admin_user(self):
        return self.user_type == 'admin' or self.is_superuser

class Learner(models.Model):
    """
    Learner/Student profile linked to Django User
    Can be associated with a partner organization
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learner_profile')
    partner = models.ForeignKey(
        'partern.TenantPartner', 
        on_delete=models.SET_NULL, 
        related_name='students',
        null=True,
        blank=True,
        help_text="Partner organization this student belongs to"
    )
    phone_number = models.CharField(max_length=15, blank=True)
    registration_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    enrolled_courses = models.ManyToManyField('courses.Course', related_name='learners', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    birth_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} (Student)"
    
    class Meta:
        verbose_name = "Learner"
        verbose_name_plural = "Learners"
        ordering = ['-created_at']
    
class Subscription(models.Model):
    """
    Subscription plan for learners
    """
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateField()
    end_date = models.DateField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Subscription of {self.learner.user.username} from {self.start_date} to {self.end_date}"
    
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        ordering = ['-start_date']
    
class Instructor(models.Model):
    """
    Instructor profile linked to Django User
    Must be associated with a partner organization
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    partner = models.ForeignKey(
        'partern.TenantPartner', 
        on_delete=models.SET_NULL, 
        related_name='instructors',
        null=True,
        blank=True,
        help_text="Partner organization this instructor belongs to"
    )
    phone_number = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='instructor_pictures/', null=True, blank=True)
    specialization = models.CharField(max_length=200, blank=True, help_text="Area of expertise")
    is_approved = models.BooleanField(default=False, help_text="Approved by partner admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} (Instructor)"
    
    class Meta:
        verbose_name = "Instructor"
        verbose_name_plural = "Instructors"
        ordering = ['-created_at']

class AccountProfile(models.Model):
    """
    Extended profile information for any user
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='extended_profile')
    bio = models.TextField(blank=True, max_length=50)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    
    class Meta:
        verbose_name = "Account Profile"
        verbose_name_plural = "Account Profiles"