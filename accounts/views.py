from django.shortcuts import render, redirect
from .models import Learner, Instructor
from .form import LearnerForm, InstructorForm, AccountProfileForm,InstructorRegistrationForm, LearnerRegistrationForm
from .serilaizer import LearnerSerializer, InstructorSerializer
from rest_framework import viewsets
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.decorator import is_learner, is_instructor, is_admin


# Create your views here.
class LearnerViewSet(viewsets.ModelViewSet):
    queryset = Learner.objects.all()
    serializer_class = LearnerSerializer

class InstructorViewSet(viewsets.ModelViewSet):
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer

def Learner_register(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'instructor':
            return redirect('course_list')
        else:
            return redirect('home')
    if request.method == 'POST':
        form = LearnerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'learner'
            user.save()
            
            # Create Learner profile
            Learner.objects.create(
                user=user,
                phone_number=form.cleaned_data.get('phone_number'),
                birth_date=form.cleaned_data.get('date_of_birth')
            )
            
            login(request, user=user)
            messages.success(request, "Registration successful.")

            if request.user.user_type == 'learner':
                return redirect('course_list')
            else:
                return redirect('home')
    else:
        form = LearnerRegistrationForm()
                    
    return render(request, 'accounts/learner_register.html', {'form': form})

def Instructor_register(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'instructor':
            return redirect('create_course')
        else:
            return redirect('home')
    if request.method == 'POST':
        form = InstructorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'instructor'
            user.save()
            
            # Create Instructor profile
            Instructor.objects.create(
                user=user,
                phone_number=form.cleaned_data.get('phone_number'),
                bio=form.cleaned_data.get('bio'),
                specialization=form.cleaned_data.get('specialization')
            )
            
            login(request, user=user)
            messages.success(request, "Registration successful.")

            if request.user.user_type == 'instructor':
                return redirect('create_course')
            else:
                return redirect('home')
    else:
        form = InstructorRegistrationForm ()
                    
    return render(request, 'accounts/instructor_register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'instructor':
            return redirect('create_course')
        else:
            return redirect('home')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user_obj = user.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                if user.user_type == 'instructor':
                    return redirect('create_course')
                else:
                    return redirect('home')
            else:
                messages.error(request, "Invalid email or password.")
        except user.DoesNotExist:
            messages.error(request, "User with this email does not exist.")
            
    return render(request, 'accounts/login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('accounts:login')

def profile(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = AccountProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = AccountProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})

#For Edithing Student Profile 
@login_required
@is_learner
def learner_edit_profile(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'learner_profile'):
        return redirect('accounts:login')
    
    learner = request.user.learner_profile
    
    if request.method == 'POST':
        form = LearnerForm(request.POST, request.FILES, instance=learner)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = LearnerForm(instance=learner)
    
    return render(request, 'accounts/learner_edit_profile.html', {'form': form})

#For Editing Instructor Profile
@login_required
@is_instructor
def instructor_edit_profile(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'instructor_profile'):
        return redirect('accounts:login')
    
    instructor = request.user.instructor_profile
    
    if request.method == 'POST':
        form = InstructorForm(request.POST, request.FILES, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = InstructorForm(instance=instructor)
    
    return render(request, 'accounts/instructor_edit_profile.html', {'form': form})