from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Company, User


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'phone', 'email', 'subscription_status', 'trial_ends_at', 'is_active')
    search_fields = ('name', 'code', 'phone', 'email')
    list_filter = ('subscription_status', 'is_active', 'skip_sundays_in_daily')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'company', 'is_active_agent')
    list_filter = ('role', 'is_active_agent', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('FinTrack Profile', {'fields': ('company', 'role', 'phone_number', 'daily_collection_target', 'is_active_agent')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('FinTrack Profile', {'fields': ('company', 'role', 'phone_number', 'daily_collection_target', 'is_active_agent')}),
    )
