from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, BaseUserManager
from django.utils import timezone
import uuid

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    User_type = (
        ('learner', 'Learner'),
        ('instructor', 'Instructor'),
        ("partner_admin", "Partner Admin"),
        ('admin', 'Admin'),
    )
    User_type_choices = models.CharField(max_length=20, choices=User_type, default='learner')
    picture_profile = models.ImageField(upload_to='Profiles',null =True, blank = True)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'#Define what will be needed to login instead of username
    REQUIRED_FIELDS = ['first_name', 'last_name', 'Phone']#Requirements when Createing Superuser
    Phone = models.CharField(max_length=15, blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name="custom_user_groups_set",
        blank=True,
        help_text="The groups this user belongs to."
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions_set",
        blank=True,
        help_text="Specific permissions for this user."
    )


    #Direct Each One one the User_type to a property to make it easier to check the type of user in the code
    @property
    def is_learner(self):
        return self.User_type_choices == 'learner'
    @property
    def is_instructor(self):
        return self.User_type_choices == 'instructor'
    @property
    def is_admin(self):
        return self.User_type_choices == 'admin'
    

   
    def __str__(self):
        return self.email

class LearnerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='Learner')
    # Add any additional fields specific to learners here
    
    phone_number = models.CharField(max_length=20)
    Reg_Number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
   
    def __str__(self):
        return f"{self.user.get_full_name()} - Learner Profile"
    
    class Meta:
        verbose_name = 'Learner'
        verbose_name_plural = 'Learners'
        ordering = ['created_at']

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - Subscription"
    
    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        ordering = ['start_date']
    
class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    # Add any additional fields specific to instructors here
    phone_number = models.CharField(max_length=20)
    bio = models.TextField(blank=True)
    Specialization = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_students(self):
        """Here we will created how to see number of student enrolled in courses of this instructor"""
    

   
    def __str__(self):
        return f"{self.user.get_full_name()} - Instructor Profile"
    
    class Meta:
        verbose_name = 'Instructor Profile'
        verbose_name_plural = 'Instructor Profiles'
        ordering = ['created_at']


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