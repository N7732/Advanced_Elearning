# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import User, LearnerProfile, Instructor, Subscription, AccountProfile

User = get_user_model()

# ==================== USER SERIALIZERS ====================

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    # Additional fields that might be required
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone = serializers.CharField(required=True, write_only=True)
    user_type = serializers.ChoiceField(choices=User.User_type, default='learner')

    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'password2', 
            'first_name', 'last_name', 'phone', 'user_type'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs

    def create(self, validated_data):
        # Remove password2 as it's not part of the model
        validated_data.pop('password2')
        phone = validated_data.pop('phone', None)
        user_type = validated_data.get('user_type', 'learner')
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['email'],  # Django requires username
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            User_type_choices=user_type
        )
        
        # Create corresponding profile based on user type
        if user_type == 'learner':
            LearnerProfile.objects.create(
                user=user,
                phone_number=phone,
                Reg_Number=f"RW{user.id}"  # Auto-generate reg number
            )
        elif user_type == 'instructor':
            Instructor.objects.create(
                user=user,
                phone_number=phone,
                bio="",
                Specialization=""
            )
        
        # Always create extended profile
        AccountProfile.objects.create(user=user)
        
        return user

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                              username=email, password=password)
            
            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "email" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed user serializer with profile information
    """
    learner_profile = serializers.SerializerMethodField()
    instructor_profile = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'User_type_choices', 'is_active', 'date_joined',
            'learner_profile', 'instructor_profile', 'subscription_status'
        ]
    
    def get_learner_profile(self, obj):
        if hasattr(obj, 'learner_profile'):
            return LearnerProfileSerializer(obj.learner_profile).data
        return None
    
    def get_instructor_profile(self, obj):
        if hasattr(obj, 'instructor_profile'):
            return InstructorProfileSerializer(obj.instructor_profile).data
        return None
    
    def get_subscription_status(self, obj):
        if hasattr(obj, 'subscription'):
            return {
                'is_active': obj.subscription.is_active,
                'end_date': obj.subscription.end_date
            }
        return {'is_active': False}
    
    def get_full_name(self, obj):
        return obj.get_full_name()

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        extra_kwargs = {
            'email': {'read_only': True}  # Email shouldn't be changed easily
        }

# ==================== PROFILE SERIALIZERS ====================

class LearnerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Learner Profile
    """
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LearnerProfile
        fields = [
            'id', 'user_email', 'user_name', 'phone_number',
            'Reg_Number', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'Reg_Number']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()
    
    def validate_phone_number(self, value):
        if value and len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value

class InstructorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Instructor Profile
    """
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Instructor
        fields = [
            'id', 'user_email', 'user_name', 'phone_number',
            'bio', 'Specialization', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()

class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for Subscription
    """
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user_email', 'user_name', 'is_active',
            'start_date', 'end_date', 'days_remaining'
        ]
        read_only_fields = ['id', 'start_date']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()
    
    def get_days_remaining(self, obj):
        if obj.end_date and obj.is_active:
            delta = obj.end_date - obj.start_date
            return delta.days
        return 0

class AccountProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Extended Account Profile
    """
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = AccountProfile
        fields = [
            'id', 'user_email', 'bio', 'profile_picture',
            'address', 'city', 'country', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']