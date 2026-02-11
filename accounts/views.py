from django.shortcuts import render, redirect

from .models import Learner, Instructor, Subscription
from .form import LearnerForm, InstructorForm, AccountProfileForm,InstructorRegistrationForm, LearnerRegistrationForm, LoginForm
from .serializer import LearnerSerializer, InstructorSerializer
from rest_framework import viewsets
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.decorator import learner_required, instructor_required, is_admin


from django.utils import timezone
from membership.models import Invitation
from partern.models import TenantPartner
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
                    if authenticated_user.is_superuser or authenticated_user.user_type == 'admin':
                         return redirect('superadmin_dashboard:overview')
                    elif authenticated_user.user_type == 'instructor':
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



# EMAIL DEALING ALL TEMPLATES AND VIEWS CAN BE ADDED HERE, SUCH AS PASSWORD RESET, ETC.
#=======================================================================================================================================


from django.contrib.auth import get_user_model
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, 
    PasswordResetCompleteView, PasswordChangeView, PasswordChangeDoneView
)
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class CustomPasswordResetView(PasswordResetView):

    subject = "Password Reset Requested"
    template_name = 'Resent_emali/password_reset_form.html'
    email_template_name = 'Resent_emali/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        
        email = form.cleaned_data.get('email')

        try:
            user = User.objects.get(email=email)
            token_generator = self.token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_url = self.request.build_absolute_uri(
                reverse_lazy('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token_generator})
            )

            context = {
                'user': user,
                'reset_url': reset_url,
                'expiry_hours': 1,
                'settings': settings,
            }
            html_message = render_to_string(self.email_template_name, context)
            text_content = strip_tags(html_message)
            email_message = EmailMultiAlternatives(
                subject=self.subject,
                body=text_content,
                from_email=settings.EMAIL_HOST_USER,
                to = [user.email],
                )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send()
        except User.DoesNotExist:
            pass # Do not reveal if email exists or not for security reasons

        messages.success(self.request, "Password reset email has been sent if the email exists in our system.")
        return super().form_valid(form)
    
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'Resent_emali/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'Resent_emali/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        if user.is_authenticated:
            logger.info(f"Password reset successful for user: {user.email}")
        messages.success(self.request, "Your password has been reset successfully.")
        return response
    
class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'Resent_emali/password_reset_complete.html'


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'Resent_emali/password_change_form.html'
    success_url = reverse_lazy('accounts:password_change_done')

    def form_valid(self, form):
        user = self.request.user
        logger.info(f"Password change successful for user: {user.email}")
        messages.success(self.request, "Your password has been changed successfully.")
        return super().form_valid(form)
    
class CustomPasswordChangeDoneView(PasswordChangeDoneView):

    template_name = 'Resent_emali/password_change_done.html'




def send_welcome_email(user):
    subject = "Welcome to Our E-Learning Platform!"
    context = {
        'user': user,
        'settings': settings,
    }
    html_message = render_to_string('Resent_emali/welcome_email.html', context)
    text_content = strip_tags(html_message)
    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email],
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()


def send_course_enrollment_email(learner, course):
    subject = f"Enrollment Confirmation for {course.title}"
    context = {
        'learner': learner,
        'course': course,
        'settings': settings,
    }
    html_message = render_to_string('Resent_emali/course_enrollment_email.html', context)
    text_content = strip_tags(html_message)
    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[learner.user.email],
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()

def instructor_invitation_email(instructor, invitation):
    subject = "You're Invited to Join as an Instructor!"
    context = {
        'instructor': instructor,
        'invitation': invitation,
        'settings': settings,
    }
    html_message = render_to_string('Resent_emali/instructor_invitation_email.html', context)
    text_content = strip_tags(html_message)
    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[instructor.email],
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()

def instructor_welcome_email(instructor):
    subject = "Welcome to Our E-Learning Platform as an Instructor!"
    context = {
        'instructor': instructor,
        'specialization': instructor.specialization,
        'pattern_type': instructor.get_pattern_type_display() if instructor.pattern_type else 'N/A',
        'settings': settings,
    }
    html_message = render_to_string('Resent_emali/instructor_welcome_email.html', context)
    text_content = strip_tags(html_message)
    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[instructor.email],
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()


def certificate_email(learner, course, certificate):
    subject = f"Congratulations on Completing {course.title}!"
    context = {
        'learner': learner,
        'course': course,
        'certificate': certificate,
        'settings': settings,
    }
    html_message = render_to_string('Resent_emali/certificate_email.html', context)
    text_content = strip_tags(html_message)
    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[learner.user.email],
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()

def update_email_to_student(course, request=None):
    """
    Sends a new course notification to all registered students and active subscribers.
    """
    instructor = course.instructor
    subject = f"New Course Alert: '{course.title}' is Now Live!"
    
    # Fetch all learners and students with active subscriptions
    learner_emails = set(Learner.objects.all().values_list('user__email', flat=True))
    active_subscriber_emails = set(Subscription.objects.filter(active=True).values_list('learner__user__email', flat=True))
    
    all_emails = list(learner_emails | active_subscriber_emails)
    
    if not all_emails:
        logger.info(f"No recipients found for course notification: {course.title}")
        return

    context = {
        'instructor': instructor,
        'course': course,
        'settings': settings,
        'request': request,
    }
    
    html_message = render_to_string('Resent_emali/new_course_notification_email.html', context)
    text_content = strip_tags(html_message)
    
    # Send in bulk using BCC to protect privacy
    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[settings.EMAIL_HOST_USER],
        bcc=all_emails,
        headers={
            'X-Email-Category': 'Promotion',
            'Precedence': 'bulk',
            'Auto-Submitted': 'auto-generated'
        }
    )
    email_message.attach_alternative(html_message, "text/html")
    
    try:
        email_message.send()
        logger.info(f"Successfully sent notification for '{course.title}' to {len(all_emails)} recipients.")
    except Exception as e:
        logger.error(f"Error sending course notification email: {str(e)}")

        context = {
        'instructor': instructor,
        'course': course,
        'settings': settings,
    }
        
    html_message = render_to_string('Resent_emali/new_course_notification_email.html', context)
    text_content = strip_tags(html_message)
    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[instructor.email],
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()
    