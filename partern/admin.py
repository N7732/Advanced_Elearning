from django.contrib import admin
from .models import TenantPartner

# Customize admin site
admin.site.site_header = "E-Learning Platform Admin"
admin.site.site_title = "E-Learning Platform Admin Portal"
admin.site.index_title = "Welcome to E-Learning Platform Admin"

@admin.register(TenantPartner)
class TenantPartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'pattern_type', 'active', 'admin_user', 'max_users', 'start_date', 'end_date', 'created_at']
    list_filter = ['active', 'pattern_type', 'start_date']
    search_fields = ['name', 'contact_email']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'pattern_type', 'contact_email', 'logo')
        }),
        ('Dates & Status', {
            'fields': ('start_date', 'end_date', 'active', 'max_users', 'is_approved_by_RDB', 'structure_type')
        }),
        ('Administration', {
            'fields': ('admin_user', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


