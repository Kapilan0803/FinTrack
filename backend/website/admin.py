from django.contrib import admin
from .models import DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_name', 'phone', 'email', 'city', 'is_contacted', 'created_at')
    search_fields = ('name', 'company_name', 'phone', 'email', 'city')
    list_filter = ('is_contacted', 'created_at')
