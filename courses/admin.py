from django.contrib import admin
from django.db import models
from .models import Course, Module, Lesson, Quizes, QuizQuestion, Enrollment, Certificate, CoursePrerequisite

class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1

class CoursePrerequisiteInline(admin.TabularInline):
    model = CoursePrerequisite
    fk_name = 'course'
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'partner', 'difficulty_level', 'is_published', 'is_free', 'created_at')
    list_filter = ('is_published', 'is_free', 'difficulty_level', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CoursePrerequisiteInline, ModuleInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'instructor_profile'):
            return qs.filter(instructor=request.user.instructor_profile)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not obj.instructor and hasattr(request.user, 'instructor_profile'):
            obj.instructor = request.user.instructor_profile
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'instructor' in form.base_fields:
                form.base_fields['instructor'].disabled = True
                form.base_fields['instructor'].required = False
            if 'partner' in form.base_fields:
                 # Optional: also restrict partner if needed
                 pass
        return form

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'instructor_profile'):
            return qs.filter(course__instructor=request.user.instructor_profile)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course" and not request.user.is_superuser:
            if hasattr(request.user, 'instructor_profile'):
                kwargs["queryset"] = Course.objects.filter(instructor=request.user.instructor_profile)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 1

@admin.register(Quizes)
class QuizesAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'course', 'module', 'lesson', 'order', 'is_locked')
    list_filter = ('course', 'module', 'is_locked')
    inlines = [QuizQuestionInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'instructor_profile'):
            instructor = request.user.instructor_profile
            # Filter quizzes linked to instructor's courses via any path
            return qs.filter(
                models.Q(course__instructor=instructor) |
                models.Q(module__course__instructor=instructor) |
                models.Q(lesson__module__course__instructor=instructor)
            ).distinct()
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
            
        instructor = getattr(request.user, 'instructor_profile', None)
        if instructor:
            if db_field.name == "lesson":
                 kwargs["queryset"] = Lesson.objects.filter(module__course__instructor=instructor)
            elif db_field.name == "module":
                 kwargs["queryset"] = Module.objects.filter(course__instructor=instructor)
            elif db_field.name == "course":
                 kwargs["queryset"] = Course.objects.filter(instructor=instructor)
                 
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('learner', 'course', 'status', 'progress', 'score', 'completed', 'enrolled_at')
    list_filter = ('status', 'completed', 'enrolled_at')
    search_fields = ('learner__user__username', 'course__title')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'instructor_profile'):
            return qs.filter(course__instructor=request.user.instructor_profile)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course" and not request.user.is_superuser:
             if hasattr(request.user, 'instructor_profile'):
                 kwargs["queryset"] = Course.objects.filter(instructor=request.user.instructor_profile)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'certificate_code', 'issue_date')
    search_fields = ('certificate_code', 'enrollment__learner__user__username')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'instructor_profile'):
            return qs.filter(enrollment__course__instructor=request.user.instructor_profile)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "enrollment" and not request.user.is_superuser:
             if hasattr(request.user, 'instructor_profile'):
                 kwargs["queryset"] = Enrollment.objects.filter(course__instructor=request.user.instructor_profile)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)