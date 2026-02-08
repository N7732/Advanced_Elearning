from django.shortcuts import render, redirect
from .models import Learner, Instructor
from .form import LearnerForm, InstructorForm, AccountProfileForm,InstructorRegistrationForm, LearnerRegistrationForm, LoginForm
from .serializer import LearnerSerializer, InstructorSerializer
from rest_framework import viewsets
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.decorator import learner_required, instructor_required, is_admin


from django.utils import timezone
from membership.models import Invitation
# Create your views here.

class LearnerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Learner instances.
    """
    queryset = Learner.objects.all()
    serializer_class = LearnerSerializer

class InstructorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Instructor instances.
    """
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer

def learner_register(request, token=None):
    """
    Handles the registration process for learners, optionally using an invitation token.

    Args:
        request (HttpRequest): The request object.
        token (str, optional): The invitation token. Defaults to None.

    Returns:
        HttpResponse: The rendered registration page or a redirect.
    """
    if request.user.is_authenticated:
        if request.user.user_type == 'instructor':
            return redirect('course_list')
        else:
            return redirect('home')
    
    initial_data = {}
    invitation_partner = None
    
    # Handle optional invitation for learners

    if token:
        try:
            invitation = Invitation.objects.get(token=token, used=False)
            if invitation.expires_at >= timezone.now():
                initial_data['email'] = invitation.email
                initial_data['partner'] = invitation.partner
                invitation_partner = invitation.partner

        except Invitation.DoesNotExist:
            pass # Fail silently for valid public registration fallback, or handle error if strict invite needed

    if request.method == 'POST':
        form = LearnerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # If invited, verify email again or just proceed
            
            user = form.save(commit=False)
            user.user_type = 'learner'
            user.save()
            
            # prioritized invitation partner if exists
            partner = None
            if invitation_partner:
                partner = invitation_partner
                invitation.used = True
                invitation.save()
            
            # Create Learner profile
            learner, created = Learner.objects.get_or_create(user=user)
            learner.phone_number = form.cleaned_data.get('phone_number')
            learner.birth_date = form.cleaned_data.get('date_of_birth')
            learner.partner = partner
            learner.registration_number = f"REG-{int(timezone.now().timestamp())}"
            learner.save()
            
            login(request, user=user)
            messages.success(request, "Registration successful.")

            return redirect('home')
    else:
        form = LearnerRegistrationForm(initial=initial_data)
                    
    return render(request, 'accounts/learner_register.html', {'form': form})

def instructor_register(request, token=None):
    """
    Handles the registration process for instructors, requiring a valid invitation token.

    Args:
        request (HttpRequest): The request object.
        token (str, optional): The invitation token. Defaults to None.

    Returns:
        HttpResponse: The rendered registration page or a redirect.
    """
    if request.user.is_authenticated:
        if request.user.user_type == 'instructor':
            return redirect('instructor_dashboard')
        else:
            return redirect('home')

    # Validate token
    if not token:
        messages.error(request, "Instructor registration is by invitation only.")
        return redirect('accounts:login')
        
    try:
        invitation = Invitation.objects.get(token=token, used=False)
        if invitation.expires_at < timezone.now():
            messages.error(request, "This invitation link has expired.")
            return redirect('accounts:login')
    except Invitation.DoesNotExist:
        messages.error(request, "Invalid or used invitation link.")
        return redirect('accounts:login')

    if request.method == 'POST':
        form = InstructorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if email matches invitation (security check)
            if form.cleaned_data.get('email') != invitation.email:
                messages.error(request, "Email must match the invitation.")
                return render(request, 'accounts/instructor_register.html', {'form': form})

            user = form.save(commit=False)
            user.user_type = 'instructor'
            user.save()
            
            # Create Instructor profile
            specialization = form.cleaned_data.get('expertise_areas', '')
            professional_title = form.cleaned_data.get('professional_title', '')
            linkedin = form.cleaned_data.get('linkedin_profile', '')
            experience = form.cleaned_data.get('experience_level', '')
            
            # Combine title and bio if needed, or store in bio
            bio = form.cleaned_data.get('bio', '')
            if professional_title:
                bio = f"{professional_title}\n\n{bio}"
            if linkedin:
                bio = f"{bio}\n\nLinkedIn: {linkedin}"
                
            instructor, created = Instructor.objects.get_or_create(user=user)
            instructor.phone_number = form.cleaned_data.get('phone_number')
            instructor.bio = bio
            instructor.specialization = specialization
            instructor.partner = invitation.partner
            instructor.save()
            
            # Mark invitation as used
            invitation.used = True
            invitation.save()
            
            login(request, user=user)
            messages.success(request, "Registration successful.")

            return redirect('instructor_dashboard')
    else:
        form = InstructorRegistrationForm(initial={'email': invitation.email})
                    
    return render(request, 'accounts/instructor_register.html', {'form': form})


from django.contrib.auth import get_user_model

def user_login(request):
    """
    Handles user login.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered login page or a redirect.
    """
    if request.user.is_authenticated:
        if request.user.user_type == 'instructor':
            return redirect('instructor_dashboard')
        else:
            return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            User = get_user_model()
            try:
                user_obj = User.objects.get(email=email)
                authenticated_user = authenticate(request, username=user_obj.username, password=password)
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    if authenticated_user.user_type == 'instructor':
                        return redirect('instructor_dashboard')
                    else:
                        return redirect('home')
                else:
                    messages.error(request, "Invalid email or password.")
            except User.DoesNotExist:
                messages.error(request, "User with this email does not exist.")
    else:
        form = LoginForm()
            
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    """
    Handles user logout.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: A redirect to the login page.
    """
    logout(request)
    return redirect('accounts:login')

def profile(request):
    """
    Displays and processes the account profile form.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered profile page or a redirect.
    """
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = AccountProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile')
    else:
        form = AccountProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})

#For Edithing Student Profile 
@login_required
@learner_required
def learner_edit_profile(request):
    """
    Allows a learner to edit their specific profile details.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered edit profile page or a redirect.
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'learner_profile'):
        return redirect('accounts:login')
    
    learner = request.user.learner_profile
    
    if request.method == 'POST':
        form = LearnerForm(request.POST, request.FILES, instance=learner)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile')
    else:
        form = LearnerForm(instance=learner)
    
    return render(request, 'accounts/learner_edit_profile.html', {'form': form})

#For Editing Instructor Profile
@login_required
@instructor_required
def instructor_edit_profile(request):
    """
    Allows an instructor to edit their specific profile details.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered edit profile page or a redirect.
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'instructor_profile'):
        return redirect('accounts:login')
    
    instructor = request.user.instructor_profile
    
    if request.method == 'POST':
        form = InstructorForm(request.POST, request.FILES, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile')
    else:
        form = InstructorForm(instance=instructor)
    
    return render(request, 'accounts/instructor_edit_profile.html', {'form': form})

# For Static Pages
def about_as(request):
    """
    Renders the 'About Us' page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered about page.
    """
    return render(request, 'accounts/about.html')

def contact_as(request):
    """
    Renders the 'Contact Us' page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered contact page.
    """
    return render(request, 'accounts/contact.html')