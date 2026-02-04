from django.contrib import admin
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

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonInline]

class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 1

@admin.register(Quizes)
class QuizesAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'order')
    inlines = [QuizQuestionInline]

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('learner', 'course', 'status', 'progress', 'score', 'completed', 'enrolled_at')
    list_filter = ('status', 'completed', 'enrolled_at')
    search_fields = ('learner__user__username', 'course__title')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'certificate_code', 'issue_date')
    search_fields = ('certificate_code', 'enrollment__learner__user__username')