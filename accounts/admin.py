from django.contrib import admin
from .models import Learner, Instructor, Subscription, AccountProfile

admin.site.site_header = "E-Learning Platform Admin"
admin.site.site_title = "E-Learning Platform Admin Portal"  
admin.site.index_title = "Welcome to E-Learning Platform Admin"

@admin.register(Learner)
class LearnerAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'get_email', 'partner', 'phone_number', 'created_at']
    list_filter = ['partner', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['enrolled_courses']
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'get_email', 'partner', 'specialization', 'is_approved', 'created_at']
    list_filter = ['partner', 'is_approved', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'specialization']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['learner', 'start_date', 'end_date', 'active', 'created_at']
    list_filter = ['active', 'start_date', 'end_date']
    search_fields = ['learner__user__username', 'learner__user__email']
    readonly_fields = ['created_at']

@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country', 'created_at']
    list_filter = ['country', 'created_at']
    search_fields = ['user__username', 'user__email', 'city', 'country']
    readonly_fields = ['created_at', 'updated_at']



