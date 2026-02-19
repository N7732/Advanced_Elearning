# views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout
from rest_framework.authtoken.models import Token

from .serializer import UserRegistrationSerializer
from .models import User, LearnerProfile, Instructor, Subscription, AccountProfile
from .serializer import AccountProfileSerializer, LearnerProfileSerializer, InstructorProfileSerializer, SubscriptionSerializer, UserDetailSerializer, UserRegistrationSerializer, UserLoginSerializer, UserUpdateSerializer
from .permission import IsLearner, IsInstructor, IsAdmin, IsOwnerOrReadOnly, IsProfileOwner, CanManageSubscription

# ==================== AUTHENTICATION VIEWS ====================

class RegisterView(generics.CreateAPIView):
    """
    Register a new user
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            "user": UserDetailSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key,
            "message": "User created successfully"
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    """
    Login user
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            "user": UserDetailSerializer(user).data,
            "token": token.key
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    """
    Logout user
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        logout(request)
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)

# ==================== USER VIEWS ====================

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(UserDetailSerializer(instance).data)

# ==================== LEARNER PROFILE VIEWS ====================

class LearnerProfileListView(generics.ListAPIView):
    """
    List all learner profiles (admin only)
    """
    queryset = LearnerProfile.objects.all()
    serializer_class = LearnerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

class LearnerProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update learner profile
    """
    queryset = LearnerProfile.objects.all()
    serializer_class = LearnerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwner]

    def get_queryset(self):
        # Filter to only show learner profiles
        return LearnerProfile.objects.filter(user__User_type_choices='learner')

class CurrentLearnerProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user's learner profile
    """
    serializer_class = LearnerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsLearner]

    def get_object(self):
        return self.request.user.learner_profile

# ==================== INSTRUCTOR PROFILE VIEWS ====================

class InstructorProfileListView(generics.ListAPIView):
    """
    List all instructor profiles
    """
    queryset = Instructor.objects.all()
    serializer_class = InstructorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

class InstructorProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update instructor profile
    """
    queryset = Instructor.objects.all()
    serializer_class = InstructorProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwner]

    def get_queryset(self):
        return Instructor.objects.filter(user__User_type_choices='instructor')

class CurrentInstructorProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user's instructor profile
    """
    serializer_class = InstructorProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def get_object(self):
        return self.request.user.instructor_profile

# ==================== SUBSCRIPTION VIEWS ====================

class SubscriptionListView(generics.ListCreateAPIView):
    """
    List all subscriptions or create new one (admin only)
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageSubscription]

class SubscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a subscription
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

class UserSubscriptionView(generics.RetrieveAPIView):
    """
    Get current user's subscription status
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        subscription, created = Subscription.objects.get_or_create(
            user=self.request.user,
            defaults={'is_active': False}
        )
        return subscription

# ==================== ACCOUNT PROFILE VIEWS ====================

class AccountProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update account profile
    """
    serializer_class = AccountProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = AccountProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile